from datetime import timedelta

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from bookings.models import Booking
from core.assets import ASSETS
from facilities.availability import take_hold
from facilities.models import Facility, Tariff, Unit
from payments.models import Payment

from .factories import booking_template, facility, role, unit, user


class SeedAssetsCommandTests(TestCase):
    def setUp(self):
        for index in range(4):
            facility(f'seed-{index}')

    def sample_units(self):
        return Unit.objects.filter(code__startswith='sample-')

    def test_creates_fifteen_sample_assets_across_five_categories(self):
        call_command('seed_assets')
        self.assertEqual(self.sample_units().count(), 15)
        for category in ('land', 'ponds', 'markets', 'kheyaghat', 'auditorium'):
            self.assertEqual(
                self.sample_units().filter(asset_category=category).count(), 3)
        self.assertEqual(Tariff.objects.filter(unit__in=self.sample_units()).count(), 45)
        self.assertEqual(Facility.objects.count(), 4)

    def test_second_run_is_idempotent_and_preserves_records(self):
        call_command('seed_assets')
        call_command('seed_assets')
        self.assertEqual(self.sample_units().count(), 15)
        self.assertEqual(Facility.objects.count(), 4)

    def test_existing_units_are_not_replaced(self):
        call_command('seed_assets')
        pond = self.sample_units().get(code='sample-ponds-1')
        pond.name = 'Renamed pond'
        pond.save(update_fields=['name'])
        call_command('seed_assets')
        pond.refresh_from_db()
        self.assertEqual(pond.name, 'Renamed pond')

    def test_requires_the_four_managed_facilities(self):
        Facility.objects.all().delete()
        with self.assertRaises(CommandError):
            call_command('seed_assets')


class SixCategoryCatalogueTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.fac = facility('six-cat')
        cls.units = {}
        for index, asset in enumerate(ASSETS):
            code = asset['code']
            cls.units[code] = unit(
                cls.fac, f'{code[:4].upper()}{index}', kind='room',
                asset_category=code)

    def test_every_asset_category_is_publicly_browsable(self):
        day = (timezone.localdate() + timedelta(days=2)).isoformat()
        end = (timezone.localdate() + timedelta(days=3)).isoformat()
        for asset in ASSETS:
            with self.subTest(asset=asset['code']):
                response = self.client.get('/user/', {
                    'asset': asset['code'], 'check_in': day,
                    'check_out': end, 'guests': 1,
                })
                self.assertEqual(response.status_code, 200)
                expected = (self.units[asset['code']].facility.name
                            if asset['code'] == 'dakbungalow'
                            else self.units[asset['code']].name)
                self.assertContains(response, expected)


class DirectFlowEndToEndTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.template = booking_template()
        cls.citizen = user('e2e-citizen', role('citizen'))
        cls.fac = facility('e2e')
        cls.pond = unit(cls.fac, 'PND1', kind='asset', asset_category='ponds')

    def setUp(self):
        self.client.force_login(self.citizen)
        self.day = timezone.localdate() + timedelta(days=5)
        self.next_day = self.day + timedelta(days=1)

    def make_draft(self, flow='direct', unit=None, **overrides):
        unit = unit or self.pond
        payload = {
            'facility': self.fac.pk, 'unit': unit.pk, 'category': 'citizen',
            'check_in': self.day.isoformat(), 'check_out': self.next_day.isoformat(),
            'guests': 1, 'slot': '', 'flow': flow,
        }
        payload.update(overrides)
        return self.client.post(f'/user/assets/{unit.pk}/', payload)

    def submit_details(self, **overrides):
        payload = {
            'purpose': 'Sample family visit', 'guests': 1,
            'contact_phone': '01000000000', 'national_id': '1234567890123',
            'office_id': '', 'notes': '', 'terms': 'on',
        }
        payload.update(overrides)
        return self.client.post('/book/details/', payload)

    def test_direct_flow_reaches_simulated_checkout(self):
        response = self.make_draft()
        self.assertEqual(response.status_code, 302)
        response = self.submit_details()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/pay/'))
        booking = Booking.objects.get(applicant=self.citizen)
        self.assertEqual(booking.payment_flow, 'direct')
        self.assertEqual(booking.status, 'submitted')
        payment = Payment.objects.get(booking=booking)
        self.assertEqual(response.url, f'/pay/{payment.txn_id}/')

    def test_approval_first_flow_goes_to_submitted_and_cannot_pay_early(self):
        response = self.make_draft(flow='approval_first')
        self.assertEqual(response.status_code, 302)
        response = self.submit_details()
        self.assertEqual(response.status_code, 302)
        self.assertIn('/submitted/', response.url)
        booking = Booking.objects.get(applicant=self.citizen)
        self.assertEqual(booking.payment_flow, 'approval_first')
        self.assertFalse(booking.can_pay)
        self.assertFalse(Payment.objects.filter(booking=booking).exists())

    def test_citizen_details_require_a_national_id(self):
        self.make_draft()
        response = self.submit_details(national_id='')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Booking.objects.filter(applicant=self.citizen).exists())

    def test_government_category_accepts_an_office_id(self):
        self.make_draft(category='government')
        response = self.submit_details(national_id='', office_id='OFFICE-77')
        self.assertEqual(response.status_code, 302)
        booking = Booking.objects.get(applicant=self.citizen)
        self.assertEqual(booking.category, 'government')
        self.assertEqual(booking.office_id, 'OFFICE-77')

    def test_invalid_nid_is_rejected(self):
        self.make_draft()
        response = self.submit_details(national_id='12ab')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Booking.objects.filter(applicant=self.citizen).exists())

    def test_guests_over_capacity_are_rejected_at_draft(self):
        response = self.make_draft(guests=self.pond.capacity + 1)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Booking.objects.filter(applicant=self.citizen).exists())

    def test_inventory_taken_before_details_blocks_submission(self):
        self.make_draft()
        take_hold(self.pond, [self.day], '', timezone.now() + timedelta(hours=2))
        response = self.submit_details()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Booking.objects.filter(applicant=self.citizen).exists())

    def test_conflicting_dates_are_rejected_at_draft(self):
        take_hold(self.pond, [self.day], '', timezone.now() + timedelta(hours=2))
        response = self.make_draft()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Booking.objects.filter(applicant=self.citizen).exists())

    def test_permit_stays_locked_until_approval_even_after_direct_payment(self):
        from payments import gateway
        self.make_draft()
        self.submit_details()
        booking = Booking.objects.get(applicant=self.citizen)
        payment = Payment.objects.get(booking=booking)
        payload = gateway.callback_payload(payment, 'pay')
        result, _ = gateway.handle_callback(payload, gateway.sign_payload(payload))
        self.assertEqual(result, 'confirmed')
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'submitted')
        self.assertIsNone(booking.permit_issued_at)
        self.assertFalse(booking.permit_no)
