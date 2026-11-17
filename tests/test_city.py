import io

import pypdf
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from accounts.demo import DEMO_PASSWORD
from accounts.models import User
from notifications.models import Notification
from organizations.models import Organization
from services.models import ServiceApplication, ServiceForm
from tests import factories


class CityPortalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_organizations', verbosity=0)

    def test_root_opens_the_city_portal(self):
        response = self.client.get('/')
        self.assertRedirects(response, '/dscc/')

    def test_city_home_shows_the_head_label(self):
        response = self.client.get('/dscc/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['org'].code, 'dscc')
        self.assertContains(response, 'Dhaka South City Corporation')
        self.assertContains(response, 'Mayor / Administrator')

    def test_city_home_in_bangla_shows_the_bangla_title(self):
        session = self.client.session
        session['gzp_lang'] = 'bn'
        session.save()
        response = self.client.get('/dscc/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ঢাকা দক্ষিণ সিটি কর্পোরেশন')
        self.assertContains(response, 'সমন্বিত ডিজিটাল সেবা প্ল্যাটফর্ম')

    def test_seed_creates_zones_wards_services_and_forms(self):
        org = Organization.objects.get(code='dscc')
        self.assertEqual(org.zones.count(), 10)
        self.assertEqual(org.wards.count(), 75)
        self.assertEqual(org.services.filter(is_active=True).count(), 14)
        self.assertEqual(org.forms.count(), 21)
        self.assertEqual(org.departments.count(), 16)
        self.assertIsNotNone(org.wards.get(number=1).councillor)

    def test_seed_is_idempotent(self):
        call_command('seed_organizations', verbosity=0)
        org = Organization.objects.get(code='dscc')
        self.assertEqual(org.zones.count(), 10)
        self.assertEqual(org.wards.count(), 75)
        self.assertEqual(org.services.count(), 14)
        self.assertEqual(org.forms.count(), 21)
        self.assertEqual(org.departments.count(), 16)
        self.assertEqual(
            ServiceApplication.objects.filter(organization=org).count(), 4)

    def test_login_sets_the_organisation_session(self):
        response = self.client.post('/login/', {
            'username': 'dscc_mayor', 'password': DEMO_PASSWORD})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['gzp_org'], 'dscc')

    def test_login_quick_panel_lists_city_accounts(self):
        response = self.client.get('/login/')
        labels = [group['label'] for group in response.context['demo_groups']]
        self.assertEqual(labels, ['Dhaka South City Corporation'])
        usernames = [account['username'] for group in response.context['demo_groups']
                     for account in group['accounts']]
        self.assertEqual(
            sorted(usernames),
            ['dscc_citizen', 'dscc_councillor', 'dscc_mayor', 'dscc_officer'])

    def test_demo_switch_opens_the_new_account_dashboard(self):
        response = self.client.post('/demo/switch/', {
            'username': 'dscc_mayor', 'switch': '1',
            'next': '/dscc/applications/DSCC-2026-0001/'})
        self.assertRedirects(response, '/app/city/')

        response = self.client.post('/demo/switch/', {
            'username': 'dscc_citizen', 'switch': '1',
            'next': '/dscc/applications/DSCC-2026-0001/'})
        self.assertRedirects(response, '/dscc/applications/')

    def test_quick_sign_in_still_honours_the_next_link(self):
        response = self.client.post('/demo/switch/', {
            'username': 'dscc_officer', 'next': '/app/city/queue/'})
        self.assertRedirects(response, '/app/city/queue/')

    def test_parishad_modules_are_not_part_of_this_project(self):
        self.client.force_login(User.objects.get(username='dscc_officer'))
        for path in ('/gzp/', '/user/', '/track/', '/services/', '/admin/'):
            self.assertEqual(self.client.get(path).status_code, 404)
        response = self.client.get('/app/city/')
        labels = [item['label'] for group in response.context['nav_groups']
                  for item in group['items']]
        self.assertIn('Verification queue', labels)
        self.assertNotIn('Executive summary', labels)
        self.assertNotIn('All bookings', labels)

    def test_city_pages_accept_a_stale_parishad_session(self):
        session = self.client.session
        session['gzp_org'] = 'gzp'
        session.save()
        response = self.client.get('/dscc/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['ORG'].code, 'dscc')
        self.assertContains(response, 'org-city')


class CityApplicationFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_organizations', verbosity=0)
        cls.org = Organization.objects.get(code='dscc')
        cls.form = ServiceForm.objects.filter(organization=cls.org).order_by('sl').first()
        cls.citizen = User.objects.get(username='dscc_citizen')
        cls.councillor = User.objects.get(username='dscc_councillor')
        cls.officer = User.objects.get(username='dscc_officer')
        cls.mayor = User.objects.get(username='dscc_mayor')
        cls.ward = cls.org.wards.get(number=1)

    def _payload(self):
        data = {'ward': self.ward.pk}
        for index, label in enumerate(self.form.field_list(), start=1):
            if 'attach' in label.lower():
                continue
            data[f'f{index}'] = f'Test value {index}'
        return data

    def _submit(self):
        self.client.force_login(self.citizen)
        self.client.post(f'/dscc/forms/{self.form.pk}/fill/', self._payload())
        return ServiceApplication.objects.order_by('-id').first()

    def test_form_library_lists_city_forms(self):
        response = self.client.get('/dscc/forms/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_count'], 21)
        self.assertContains(response, 'Fill online')

    def test_blank_city_pdf_uses_the_city_letterhead(self):
        response = self.client.get(f'/services/forms/{self.form.pk}/blank/')
        self.assertEqual(response.status_code, 200)
        reader = pypdf.PdfReader(io.BytesIO(response.content))
        text = reader.pages[0].extract_text()
        self.assertIn('DHAKA SOUTH CITY CORPORATION', text)
        self.assertIn('DSCC', text)

    def test_fill_page_requires_sign_in(self):
        response = self.client.get(f'/dscc/forms/{self.form.pk}/fill/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_fill_page_renders_an_editable_paper_form(self):
        self.client.force_login(self.citizen)
        response = self.client.get(f'/dscc/forms/{self.form.pk}/fill/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['fields']), len(self.form.field_list()))
        self.assertContains(response, 'city-fill-form')
        self.assertContains(response, self.form.title)

    def test_submitting_creates_an_application_and_first_action(self):
        before = ServiceApplication.objects.count()
        application = self._submit()
        self.assertEqual(ServiceApplication.objects.count(), before + 1)
        self.assertEqual(application.status, 'submitted')
        self.assertEqual(application.current_order, 1)
        self.assertTrue(application.reference.startswith(
            f'DSCC-{timezone.localdate().year}-'))
        self.assertEqual(application.actions.count(), 1)
        self.assertEqual(application.ward, self.ward)

    def test_module_verifies_three_stages_then_issues_certificate(self):
        application = self._submit()

        self.client.force_login(self.councillor)
        self.client.post(f'/app/city/applications/{application.reference}/action/',
                         {'decision': 'verify', 'comments': 'Ward details checked'})
        application.refresh_from_db()
        self.assertEqual(application.current_order, 2)
        self.assertEqual(application.status, 'in_review')

        self.client.force_login(self.officer)
        self.client.post(f'/app/city/applications/{application.reference}/action/',
                         {'decision': 'verify', 'comments': 'Department checked'})
        application.refresh_from_db()
        self.assertEqual(application.current_order, 3)

        self.client.force_login(self.mayor)
        self.client.post(f'/app/city/applications/{application.reference}/action/',
                         {'decision': 'approve', 'comments': 'Approved'})
        application.refresh_from_db()
        self.assertEqual(application.status, 'approved')
        self.assertIsNotNone(application.decided_at)
        self.assertEqual(application.actions.count(), 4)

        response = self.client.get(
            f'/dscc/applications/{application.reference}/certificate.pdf')
        self.assertEqual(response.status_code, 200)
        reader = pypdf.PdfReader(io.BytesIO(response.content))
        text = reader.pages[0].extract_text()
        self.assertIn('APPROVAL CERTIFICATE', text)
        self.assertIn(application.reference, text)

    def test_next_desk_is_notified_when_a_stage_verifies(self):
        application = self._submit()
        citizen_notes = Notification.objects.filter(user=self.citizen).count()
        self.client.force_login(self.councillor)
        self.client.post(f'/app/city/applications/{application.reference}/action/',
                         {'decision': 'verify', 'comments': 'Ward details checked'})

        officer_notes = Notification.objects.filter(
            user=self.officer, body__contains=application.reference)
        self.assertEqual(officer_notes.count(), 1)
        self.assertEqual(
            Notification.objects.filter(user=self.citizen).count(), citizen_notes + 1)
        self.assertFalse(Notification.objects.filter(
            user=self.councillor, body__contains=application.reference).exists())

    def test_only_the_current_role_can_act(self):
        application = self._submit()
        self.client.force_login(self.officer)
        response = self.client.post(
            f'/app/city/applications/{application.reference}/action/',
            {'decision': 'verify'})
        self.assertEqual(response.status_code, 403)
        application.refresh_from_db()
        self.assertEqual(application.current_order, 1)

    def test_submitted_pdf_contains_the_entered_values(self):
        application = self._submit()
        self.client.force_login(self.citizen)
        response = self.client.get(
            f'/dscc/applications/{application.reference}/pdf/')
        self.assertEqual(response.status_code, 200)
        reader = pypdf.PdfReader(io.BytesIO(response.content))
        text = reader.pages[0].extract_text()
        self.assertIn('Test value 1', text)
        self.assertIn(application.reference, text)

    def test_my_applications_can_filter_by_status(self):
        self.client.force_login(self.citizen)
        response = self.client.get('/dscc/applications/?status=approved')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_status'], 'approved')
        statuses = {application.status for application in response.context['applications']}
        self.assertEqual(statuses, {'approved'})
        self.assertEqual(response.context['status_counts']['approved'], 1)

    def test_city_home_stays_a_light_service_directory(self):
        self.client.force_login(self.citizen)
        response = self.client.get('/dscc/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'my-status-strip')
        self.assertNotContains(response, 'city-service-fee')
        self.assertNotIn('status_counts', response.context)

    def test_queue_filters_by_the_users_stage(self):
        application = self._submit()
        self.client.force_login(self.councillor)
        response = self.client.get('/app/city/queue/')
        self.assertEqual(response.status_code, 200)
        references = [row['application'].reference for row in response.context['pending']]
        self.assertIn(application.reference, references)

        self.client.force_login(self.officer)
        response = self.client.get('/app/city/queue/')
        references = [row['application'].reference for row in response.context['pending']]
        self.assertNotIn(application.reference, references)

    def test_returned_application_can_be_resubmitted(self):
        application = ServiceApplication.objects.filter(
            organization=self.org, status='returned').first()
        self.assertIsNotNone(application)
        self.client.force_login(application.applicant)
        response = self.client.post(
            f'/dscc/applications/{application.reference}/resubmit/',
            {'comments': 'Attached the corrected document'})
        self.assertEqual(response.status_code, 302)
        application.refresh_from_db()
        self.assertEqual(application.status, 'submitted')
        self.assertEqual(application.current_order, 1)


class CitySetupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_organizations', verbosity=0)
        cls.org = Organization.objects.get(code='dscc')

    def test_citizen_cannot_open_the_setup_page(self):
        citizen = User.objects.get(username='dscc_citizen')
        self.client.force_login(citizen)
        self.assertEqual(self.client.get('/app/city/setup/').status_code, 403)

    def test_administrator_can_edit_the_head_label(self):
        admin_role = factories.role('admin', perms=['city.manage', 'city.view'])
        admin = factories.user('city-admin', admin_role)
        self.client.force_login(admin)
        response = self.client.get('/app/city/setup/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['ward_total'], 75)

        response = self.client.post('/app/city/setup/', {
            'action': 'org', 'head_title': 'Administrator',
            'head_name': 'Md. Test Administrator',
            'address': 'Nagor Bhaban, Dhaka',
            'phone': '02-00000000',
        })
        self.assertEqual(response.status_code, 302)
        self.org.refresh_from_db()
        self.assertEqual(self.org.head_title, 'Administrator')
        self.assertEqual(self.org.head_name, 'Md. Test Administrator')

    def test_settings_page_updates_the_head_label(self):
        admin_role = factories.role(
            'admin', perms=['accounts.manage_settings', 'city.manage'])
        admin = factories.user('settings-admin', admin_role)
        self.client.force_login(admin)
        session = self.client.session
        session['gzp_org'] = 'dscc'
        session.save()
        response = self.client.post('/app/settings/', {
            'form': 'org', 'head_title': 'Mayor / Administrator',
            'head_name': 'Md. Ashikur Rahman',
        })
        self.assertEqual(response.status_code, 302)
        self.org.refresh_from_db()
        self.assertEqual(self.org.head_title, 'Mayor / Administrator')
        self.assertEqual(self.org.head_name, 'Md. Ashikur Rahman')

    def test_zone_and_ward_can_be_added(self):
        admin_role = factories.role('admin', perms=['city.manage'])
        admin = factories.user('setup-admin', admin_role)
        self.client.force_login(admin)
        self.client.post('/app/city/setup/', {
            'action': 'zone', 'number': 11, 'name': 'Zone 11', 'name_bn': ''})
        zone = self.org.zones.get(number=11)
        self.client.post('/app/city/setup/', {
            'action': 'ward', 'number': 76, 'zone': zone.pk,
            'name': 'Ward 76', 'name_bn': '', 'councillor_name': 'Test Councillor'})
        self.assertEqual(self.org.wards.count(), 76)
        self.assertEqual(self.org.wards.get(number=76).councillor_name, 'Test Councillor')


class CityOfficesAndActsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_organizations', verbosity=0)

    def test_offices_page_lists_the_sixteen_offices_in_five_groups(self):
        response = self.client.get('/dscc/offices/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['office_count'], 16)
        self.assertEqual(len(response.context['groups']), 5)
        self.assertContains(response, 'Revenue Department')
        self.assertContains(response, 'Law Department')

    def test_offices_page_counts_the_services_of_each_office(self):
        response = self.client.get('/dscc/offices/')
        revenue = next(
            row for group in response.context['groups'] for row in group['rows']
            if row['name'] == 'Revenue Department')
        self.assertEqual(len(revenue['services']), 4)
        self.assertTrue(all(
            service['url'].startswith('/dscc/services/') for service in revenue['services']))

    def test_offices_page_in_bangla_translates_departments_and_contacts(self):
        session = self.client.session
        session['gzp_lang'] = 'bn'
        session.save()
        response = self.client.get('/dscc/offices/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'প্রকৌশল বিভাগ')
        self.assertContains(response, 'প্রধান প্রকৌশলী')
        self.assertContains(response, 'নগর ভবন · ৪র্থ তলা · কক্ষ ৪০২')
        self.assertNotContains(response, 'Engineering Department')

    def test_office_detail_page_shows_the_head_address_and_services(self):
        response = self.client.get('/dscc/offices/dscc-dept-04/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Engineering Department')
        self.assertContains(response, 'Chief Engineer')
        self.assertContains(response, 'Nagar Bhaban · 4th floor · Room 402')
        self.assertTrue(response.context['services'])

    def test_office_detail_page_returns_404_for_unknown_code(self):
        response = self.client.get('/dscc/offices/dscc-dept-99/')
        self.assertEqual(response.status_code, 404)

    def test_office_detail_page_in_bangla_translates_profile(self):
        session = self.client.session
        session['gzp_lang'] = 'bn'
        session.save()
        response = self.client.get('/dscc/offices/dscc-dept-04/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'প্রকৌশল বিভাগ')
        self.assertContains(response, 'প্রধান প্রকৌশলী')
        self.assertContains(response, 'নগর ভবন · ৪র্থ তলা · কক্ষ ৪০২')
        self.assertNotContains(response, 'Engineering Department')

    def test_acts_page_filters_gazette_law_and_rules(self):
        response = self.client.get('/dscc/acts/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 9)
        self.assertEqual([tab['count'] for tab in response.context['tabs']], [3, 3, 3])
        for code in ('gazette', 'law', 'rules'):
            filtered = self.client.get(f'/dscc/acts/?type={code}')
            self.assertEqual(filtered.status_code, 200)
            self.assertTrue(filtered.context['documents'])
            self.assertTrue(all(
                doc['category'] == code for doc in filtered.context['documents']))


class CityDashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_organizations', verbosity=0)

    def test_each_verification_role_has_its_own_city_dashboard(self):
        for username in ('dscc_councillor', 'dscc_officer', 'dscc_mayor'):
            user = User.objects.get(username=username)
            self.client.force_login(user)
            response = self.client.get('/app/city/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['org'].code, 'dscc')
            self.assertGreaterEqual(response.context['stage_count'], 3)

    def test_mayor_desk_is_the_final_stage(self):
        self.client.force_login(User.objects.get(username='dscc_mayor'))
        response = self.client.get('/app/city/')
        self.assertTrue(response.context['is_final_desk'])

    def test_councillor_desk_is_not_the_final_stage(self):
        self.client.force_login(User.objects.get(username='dscc_councillor'))
        response = self.client.get('/app/city/')
        self.assertFalse(response.context['is_final_desk'])

    def test_city_sidebar_shows_only_city_links(self):
        self.client.force_login(User.objects.get(username='dscc_officer'))
        response = self.client.get('/app/city/')
        labels = [item['label'] for group in response.context['nav_groups']
                  for item in group['items']]
        self.assertIn('Offices and departments', labels)
        self.assertIn('Acts, rules and gazettes', labels)
        self.assertNotIn('Executive summary', labels)
        self.assertNotIn('All bookings', labels)

    def test_citizen_is_sent_to_their_own_application_list(self):
        self.client.force_login(User.objects.get(username='dscc_citizen'))
        response = self.client.get('/app/city/')
        self.assertRedirects(response, '/dscc/applications/')

    def test_city_staff_landing_page_is_the_city_dashboard(self):
        self.client.force_login(User.objects.get(username='dscc_officer'))
        response = self.client.get('/app/')
        self.assertRedirects(response, '/app/city/')

    def test_organisation_switch_url_is_gone(self):
        self.client.force_login(User.objects.get(username='dscc_officer'))
        response = self.client.get('/?enter=gzp')
        self.assertRedirects(response, '/dscc/')
        self.assertNotEqual(self.client.session.get('gzp_org'), 'gzp')


class TypedFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_organizations', verbosity=0)
        cls.form = ServiceForm.objects.get(form_no='DSCC/FRM/2026/021')
        cls.citizen = User.objects.get(username='dscc_citizen')

    def _specs(self):
        return self.form.field_specs()

    def test_form_mirrors_the_pdf_sections_and_typed_fields(self):
        specs = self._specs()
        sections = [row['label'] for row in specs if row['kind'] == 'section']
        self.assertEqual(
            sections, ['Applicant', 'Permanent address', 'Guardian and attachments'])
        fields = {row['label']: row for row in specs if row['kind'] == 'field'}
        self.assertEqual(len(fields), 25)
        self.assertEqual(fields['National ID number']['type'], 'nid')
        self.assertEqual(fields['Mobile number']['type'], 'mobile')
        self.assertEqual(fields['Gender']['type'], 'radio')
        self.assertEqual(fields['Gender']['options'], ['Female', 'Male', 'Hijra'])
        self.assertEqual(len(fields['Nature of application']['options']), 6)
        self.assertTrue(fields['Guardian name (optional, if the applicant is a minor)']['optional'])
        self.assertTrue(fields['Attachments']['optional'])

    def test_fill_page_renders_native_inputs(self):
        self.client.force_login(self.citizen)
        response = self.client.get(f'/dscc/forms/{self.form.pk}/fill/')
        self.assertEqual(response.status_code, 200)
        for fragment in ('<select', 'type="radio"', 'type="date"', 'pattern="[0-9]{10,17}"'):
            self.assertContains(response, fragment)

    def test_an_unlisted_select_value_is_rejected(self):
        before = ServiceApplication.objects.count()
        self.client.force_login(self.citizen)
        payload = {row['key']: 'Sample value' for row in self._specs()
                   if row['kind'] == 'field'}
        payload.update({'f3': '1234567890123', 'f5': 'Female', 'f6': 'Islam',
                        'f7': 'A reason that is not listed', 'f10': '01711000021',
                        'f17': '1700'})
        self.client.post(f'/dscc/forms/{self.form.pk}/fill/', payload)
        self.assertEqual(ServiceApplication.objects.count(), before)

    def test_an_optional_field_can_be_left_empty(self):
        self.client.force_login(self.citizen)
        payload = {row['key']: 'Sample value' for row in self._specs()
                   if row['kind'] == 'field' and not row['optional']}
        payload.update({'f3': '1234567890123', 'f5': 'Female', 'f6': 'Islam',
                        'f7': 'Natural disaster', 'f10': '01711000021',
                        'f17': '1700'})
        response = self.client.post(f'/dscc/forms/{self.form.pk}/fill/', payload)
        self.assertEqual(response.status_code, 302)
        application = ServiceApplication.objects.order_by('-id').first()
        self.assertIn(application.reference, response['Location'])

    def test_submitted_pdf_prints_the_section_headings(self):
        self.client.force_login(self.citizen)
        payload = {row['key']: 'Sample value' for row in self._specs()
                   if row['kind'] == 'field'}
        payload.update({'f3': '1234567890123', 'f5': 'Female', 'f6': 'Islam',
                        'f7': 'Natural disaster', 'f10': '01711000021',
                        'f17': '1700'})
        self.client.post(f'/dscc/forms/{self.form.pk}/fill/', payload)
        application = ServiceApplication.objects.order_by('-id').first()
        response = self.client.get(f'/dscc/applications/{application.reference}/pdf/')
        self.assertEqual(response.status_code, 200)
        reader = pypdf.PdfReader(io.BytesIO(response.content))
        text = '\n'.join(page.extract_text() or '' for page in reader.pages)
        self.assertIn('PERMANENT ADDRESS', text)
        self.assertIn('GUARDIAN AND ATTACHMENTS', text)
        self.assertIn('Natural disaster', text)

    def test_optional_tag_is_not_printed_twice(self):
        fields = {row['label']: row for row in self._specs() if row['kind'] == 'field'}
        self.assertFalse(
            fields['Guardian name (optional, if the applicant is a minor)']['show_optional'])
        self.assertTrue(fields['Attachments']['show_optional'])

    def test_bangla_page_translates_labels_and_keeps_english_values(self):
        self.client.force_login(self.citizen)
        session = self.client.session
        session['gzp_lang'] = 'bn'
        session.save()
        response = self.client.get(f'/dscc/forms/{self.form.pk}/fill/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'জাতীয় পরিচয়পত্র নম্বর')
        self.assertContains(response, 'ধর্ম')
        self.assertContains(response, 'value="Female"')
        self.assertContains(response, 'মহিলা')
        self.assertContains(response, 'value="Natural disaster"')
        self.assertNotContains(response, 'Guardian name (optional, if the applicant is a minor)')

    def test_saved_application_lists_parsed_labels(self):
        self.client.force_login(self.citizen)
        payload = {row['key']: 'Sample value' for row in self._specs()
                   if row['kind'] == 'field'}
        payload.update({'f3': '1234567890123', 'f5': 'Female', 'f6': 'Islam',
                        'f7': 'Natural disaster', 'f10': '01711000021',
                        'f17': '1700'})
        self.client.post(f'/dscc/forms/{self.form.pk}/fill/', payload)
        application = ServiceApplication.objects.order_by('-id').first()
        labels = [label for label, _value in application.field_values()]
        self.assertIn('Mobile number', labels)
        self.assertNotIn('Mobile number|mobile', labels)
        self.assertIn(('Gender', 'Female'), application.field_values())

    def test_application_saved_with_raw_typed_keys_still_reads(self):
        application = ServiceApplication(
            reference='DSCC-2026-9001', organization=self.citizen.organization,
            form=self.form, applicant=self.citizen,
            data={'Gender|radio|Female;Male;Hijra': 'Hijra',
                  'Mobile number|mobile': '01711000021'})
        self.assertIn(('Gender', 'Hijra'), application.field_values())
        self.assertIn(('Mobile number', '01711000021'), application.field_values())


class CityAttachmentAndPaymentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_organizations', verbosity=0)
        cls.org = Organization.objects.get(code='dscc')
        cls.form = ServiceForm.objects.filter(
            organization=cls.org, service__code='trade-licence').order_by('sl').first()
        cls.citizen = User.objects.get(username='dscc_citizen')

    def _payload(self):
        return {
            row['key']: 'Sample value'
            for row in self.form.field_specs()
            if row['kind'] == 'field' and row['type'] != 'attach'
        }

    def _submit(self, **extra):
        self.client.force_login(self.citizen)
        response = self.client.post(
            f'/dscc/forms/{self.form.pk}/fill/', {**self._payload(), **extra})
        self.assertEqual(response.status_code, 302)
        self.last_response = response
        return ServiceApplication.objects.order_by('-id').first()

    def test_uploaded_document_is_saved_listed_and_downloadable(self):
        upload = SimpleUploadedFile(
            'trade-licence.pdf', b'%PDF-1.4 sample', content_type='application/pdf')
        application = self._submit(f11=upload)
        document = application.attachments.get()
        self.assertEqual(document.original_name, 'trade-licence.pdf')
        self.assertEqual(document.field_label, 'Attachments')
        self.assertIn(('Attachments', '1 file(s) attached'), application.field_values())

        page = self.client.get(f'/dscc/applications/{application.reference}/')
        self.assertContains(page, 'Attached documents')
        self.assertContains(page, 'trade-licence.pdf')

        download = self.client.get(
            f'/dscc/applications/{application.reference}/attachments/{document.pk}/')
        self.assertEqual(download.status_code, 200)
        self.assertEqual(b''.join(download.streaming_content), b'%PDF-1.4 sample')

    def test_a_disallowed_file_type_is_rejected(self):
        before = ServiceApplication.objects.count()
        upload = SimpleUploadedFile(
            'malware.exe', b'MZ', content_type='application/octet-stream')
        self.client.force_login(self.citizen)
        response = self.client.post(
            f'/dscc/forms/{self.form.pk}/fill/', {**self._payload(), 'f11': upload})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ServiceApplication.objects.count(), before)

    def _approve(self, application):
        ServiceApplication.objects.filter(pk=application.pk).update(status='approved')
        application.refresh_from_db()

    def test_fee_is_locked_until_final_approval(self):
        application = self._submit()
        page = self.client.get(f'/dscc/applications/{application.reference}/pay/')
        self.assertRedirects(
            page, f'/dscc/applications/{application.reference}/')
        self.assertFalse(application.payments.exists())

        with self.settings(DEMO_MODE=False):
            page = self.client.get(
                f'/dscc/applications/{application.reference}/pay/?demo=1')
        self.assertRedirects(
            page, f'/dscc/applications/{application.reference}/')
        self.assertFalse(application.payments.exists())

    def test_demo_submission_opens_sslcommerz_payment(self):
        application = self._submit()
        pay_url = (f'/dscc/applications/{application.reference}/pay/'
                   '?demo=1&method=sslcommerz')
        self.assertTrue(self.last_response.url.startswith(pay_url))
        page = self.client.get(self.last_response.url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'value="sslcommerz" checked')
        self.assertContains(page, 'pay-walkthrough')

    def test_real_mode_submission_waits_for_approval(self):
        with self.settings(DEMO_MODE=False):
            application = self._submit()
        self.assertRedirects(
            self.last_response, f'/dscc/applications/{application.reference}/')

    def test_walkthrough_direct_payment_skips_approval(self):
        application = self._submit()
        detail = self.client.get(f'/dscc/applications/{application.reference}/')
        self.assertContains(detail, 'Payment opens after final approval.')
        self.assertContains(detail, 'Pay now, skip verification')
        self.assertNotContains(detail, 'bi-credit-card')

        page = self.client.get(
            f'/dscc/applications/{application.reference}/pay/?demo=1')
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'pay-walkthrough')

        response = self.client.post(
            f'/dscc/applications/{application.reference}/pay/?demo=1',
            {'demo': '1', 'method': 'nagad', 'payer_ref_nagad': '01812345678'})
        self.assertRedirects(
            response, f'/dscc/applications/{application.reference}/')
        self.assertEqual(application.payments.get().method, 'nagad')
        application.refresh_from_db()
        self.assertEqual(application.status, 'submitted')

    def test_fee_is_paid_through_the_gateway_and_recorded(self):
        application = self._submit()
        self._approve(application)
        page = self.client.get(f'/dscc/applications/{application.reference}/pay/')
        self.assertEqual(page.status_code, 200)
        for brand in ('bKash', 'Nagad', 'SSLCommerz', 'Bank transfer'):
            self.assertContains(page, brand)
        self.assertContains(page, 'img/pay/bkash.png')

        response = self.client.post(
            f'/dscc/applications/{application.reference}/pay/',
            {'method': 'bkash', 'payer_ref_bkash': '01712345678'})
        self.assertRedirects(
            response, f'/dscc/applications/{application.reference}/')
        payment = application.payments.get()
        self.assertEqual(payment.method, 'bkash')
        self.assertEqual(str(payment.amount), '1500.00')
        self.assertEqual(payment.payer_ref, '5678')
        self.assertTrue(payment.transaction_id.startswith('PAY-'))

        detail = self.client.get(f'/dscc/applications/{application.reference}/')
        self.assertContains(detail, 'Paid')
        self.assertContains(detail, payment.transaction_id)

    def test_a_second_payment_is_not_accepted(self):
        application = self._submit()
        self._approve(application)
        self.client.post(
            f'/dscc/applications/{application.reference}/pay/',
            {'method': 'nagad', 'payer_ref_nagad': '01812345678'})
        response = self.client.post(
            f'/dscc/applications/{application.reference}/pay/',
            {'method': 'bkash', 'payer_ref_bkash': '01712345678'})
        self.assertRedirects(
            response, f'/dscc/applications/{application.reference}/')
        self.assertEqual(application.payments.count(), 1)