from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from bookings.forms import ApplyForm
from .factories import facility, role, unit, user


class UserCatalogueTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.fac = facility('browse')
        cls.room = unit(cls.fac)
        cls.citizen = user('catalogue-citizen', role('citizen'))
        cls.staff = user('catalogue-staff', role('admin'))

    def test_public_can_browse_user_panel(self):
        response = self.client.get('/user/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.fac.name)

    def test_asset_detail_is_public_but_reservation_requires_login(self):
        self.assertEqual(self.client.get(f'/user/assets/{self.room.pk}/').status_code, 200)
        response = self.client.post(f'/user/assets/{self.room.pk}/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_staff_cannot_create_consumer_booking(self):
        self.client.force_login(self.staff)
        response = self.client.post(f'/user/assets/{self.room.pk}/')
        self.assertEqual(response.status_code, 403)

    def test_guest_count_cannot_exceed_selected_room_capacity(self):
        day = timezone.localdate() + timedelta(days=5)
        form = ApplyForm(data={
            'facility': self.fac.pk, 'unit': self.room.pk, 'category': 'citizen',
            'check_in': day.isoformat(), 'check_out': (day + timedelta(days=1)).isoformat(),
            'guests': 3, 'slot': '',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('guests', form.errors)

    def test_user_login_filters_out_official_accounts(self):
        response = self.client.get('/login/?portal=user')
        self.assertEqual(response.context['portal'], 'user')
        self.assertEqual(response.context['next'], '/user/')

    def test_registration_rejects_empty_password(self):
        response = self.client.post('/register/', {
            'first_name': 'Sample', 'last_name': 'Applicant', 'username': 'no-password',
            'email': 'sample@example.test', 'phone': '01000000000',
            'password1': '', 'password2': '',
        })
        from accounts.models import User
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='no-password').exists())

    def test_registration_returns_to_selected_asset_after_verification(self):
        target = f'/user/assets/{self.room.pk}/?guests=2'
        response = self.client.post('/register/', {
            'first_name': 'Sample', 'last_name': 'Applicant', 'username': 'new-applicant',
            'email': 'new@example.test', 'phone': '01000000000',
            'password1': 'Demo@12345', 'password2': 'Demo@12345', 'next': target,
        })
        from accounts.models import User
        applicant = User.objects.get(username='new-applicant')
        response = self.client.post('/verify-email/', {'code': applicant.otp_code})
        self.assertEqual(response.url, target)

