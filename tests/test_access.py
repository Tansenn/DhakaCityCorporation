from django.test import TestCase

from workflow import engine
from workflow.models import WorkflowTemplate

from .factories import booking, booking_template, facility, role, unit, user


class RoleAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.citizen_role = role('citizen', 'Citizen', ['bookings.view'])
        cls.citizen = user('access-citizen', cls.citizen_role)
        cls.employee = user('access-employee', role('employee', 'Employee', ['hr.self']))
        cls.management_role = role(
            'management', 'Management / Auditor',
            ['bookings.view', 'payments.view', 'mis.reports', 'mis.export',
             'mis.view_exec', 'workflow.view'], read_only=True)
        cls.management = user('access-management', cls.management_role)
        cls.admin_role = role(
            'admin', 'System Administrator',
            ['workflow.view', 'workflow.manage', 'accounts.manage_settings'])
        cls.admin = user('access-admin', cls.admin_role)
        cls.fac_a = facility('access-a')
        cls.fac_b = facility('access-b')
        cls.unit_a = unit(cls.fac_a, 'R1')
        cls.reception = user(
            'access-reception',
            role('reception', 'Reception',
                 ['bookings.view', 'bookings.reception']),
            facility=cls.fac_a)

    def test_citizen_cannot_open_staff_portal(self):
        self.client.force_login(self.citizen)
        self.assertEqual(self.client.get('/app/').status_code, 403)

    def test_staff_cannot_open_citizen_portal(self):
        self.client.force_login(self.management)
        self.assertEqual(self.client.get('/citizen/').status_code, 403)
        self.assertEqual(
            self.client.get(f'/book/{self.fac_a.code}/').status_code, 403)

    def test_staff_can_open_dashboard(self):
        self.client.force_login(self.management)
        self.assertEqual(self.client.get('/app/').status_code, 200)

    def test_management_is_read_only_for_writes(self):
        b = booking(self.citizen, self.unit_a, status='submitted')
        self.client.force_login(self.management)
        response = self.client.post(
            f'/bookings/{b.pk}/cancel/', {'reason': 'attempted write'})
        self.assertEqual(response.status_code, 302)
        b.refresh_from_db()
        self.assertEqual(b.status, 'submitted')

    def test_management_cannot_open_refund_processing(self):
        self.client.force_login(self.management)
        self.assertEqual(self.client.get('/app/refunds/').status_code, 403)

    def test_report_permissions_are_enforced(self):
        self.client.force_login(self.employee)
        self.assertEqual(self.client.get('/app/mis/reports/').status_code, 403)
        self.assertEqual(
            self.client.get('/app/mis/reports/export/?report=bookings').status_code, 403)
        self.client.force_login(self.management)
        self.assertEqual(self.client.get('/app/mis/reports/').status_code, 200)
        export = self.client.get('/app/mis/reports/export/?report=bookings')
        self.assertEqual(export.status_code, 200)
        self.assertIn('text/csv', export['Content-Type'])

    def test_admin_cannot_act_on_a_step_of_another_role(self):
        booking_template()
        b = booking(self.citizen, self.unit_a)
        instance = engine.start(
            WorkflowTemplate.objects.get(code='booking'),
            b, {'unit_kind': 'room', 'amount': 5000}, self.citizen)
        task = instance.tasks.get(status='pending')
        self.client.force_login(self.admin)
        # Admin has workflow.manage (so the page opens) but the engine still
        # refuses the decision because the task belongs to the Booking Desk role.
        self.assertEqual(self.client.get(f'/app/tasks/{task.pk}/').status_code, 200)
        response = self.client.post(
            f'/app/tasks/{task.pk}/decide/',
            {'decision': 'forward', 'comments': 'admin attempt'})
        self.assertEqual(response.status_code, 403)
        task.refresh_from_db()
        self.assertEqual(task.status, 'pending')

    def test_reception_is_scoped_to_its_facility(self):
        own = booking(self.citizen, self.unit_a, status='paid')
        foreign = booking(self.citizen, unit(self.fac_b, 'R9'), status='paid')
        self.client.force_login(self.reception)
        self.assertEqual(self.client.get(f'/app/bookings/{own.pk}/').status_code, 200)
        self.assertEqual(
            self.client.get(f'/app/bookings/{foreign.pk}/').status_code, 403)
        self.assertEqual(self.client.get('/app/reception/').status_code, 200)

    def test_citizen_cannot_use_admin_settings(self):
        self.client.force_login(self.citizen)
        self.assertEqual(self.client.get('/app/settings/').status_code, 403)

    def test_anonymous_redirected_to_login(self):
        response = self.client.get('/app/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_nav_hides_links_without_permission(self):
        from accounts.nav import build_nav

        labels = [item['label'] for group in build_nav(self.employee)
                  for item in group['items']]
        self.assertIn('Dashboard', labels)
        self.assertNotIn('Payments & reconciliation', labels)
        self.assertNotIn('Executive dashboard', labels)
