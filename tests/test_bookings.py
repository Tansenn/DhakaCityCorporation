from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from bookings.models import Booking
from facilities import availability
from facilities.models import InventoryLock
from payments.gateway import expire_payment_windows
from workflow.models import WorkflowTemplate

from .factories import booking, facility, role, unit, user


class DoubleBookingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.fac = facility('conflict')
        cls.room = unit(cls.fac, 'R1')
        cls.other_room = unit(cls.fac, 'R2')
        cls.hall = unit(cls.fac, 'H1', 'hall', amount='8000.00')
        cls.citizen = user('citizen-x', role('citizen'))

    def test_second_active_hold_on_same_room_is_rejected(self):
        start = timezone.localdate() + timedelta(days=3)
        days = [start, start + timedelta(days=1)]
        availability.take_hold(self.room, days, '', timezone.now() + timedelta(hours=2))
        self.assertFalse(availability.is_free(
            self.room, start, start + timedelta(days=2)))
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                availability.take_hold(
                    self.room, days, '', timezone.now() + timedelta(hours=2))

    def test_overlapping_night_is_rejected_but_adjacent_night_is_free(self):
        start = timezone.localdate() + timedelta(days=6)
        availability.take_hold(
            self.room, [start, start + timedelta(days=1)], '',
            timezone.now() + timedelta(hours=2))
        self.assertFalse(availability.is_free(
            self.room, start + timedelta(days=1), start + timedelta(days=3)))
        self.assertTrue(availability.is_free(
            self.room, start + timedelta(days=2), start + timedelta(days=4)))

    def test_other_room_stays_available(self):
        start = timezone.localdate() + timedelta(days=3)
        availability.take_hold(
            self.room, [start], '', timezone.now() + timedelta(hours=2))
        self.assertTrue(availability.is_free(
            self.other_room, start, start + timedelta(days=1)))

    def test_hall_slots_are_independent(self):
        day = timezone.localdate() + timedelta(days=4)
        availability.take_hold(
            self.hall, [day], 'morning', timezone.now() + timedelta(hours=2))
        self.assertFalse(availability.is_free(
            self.hall, day, day + timedelta(days=1), 'morning'))
        self.assertTrue(availability.is_free(
            self.hall, day, day + timedelta(days=1), 'evening'))

    def test_released_lock_frees_the_inventory(self):
        start = timezone.localdate() + timedelta(days=8)
        locks = availability.take_hold(
            self.room, [start], '', timezone.now() + timedelta(hours=2))
        locks[0].released = True
        locks[0].save(update_fields=['released'])
        self.assertTrue(availability.is_free(
            self.room, start, start + timedelta(days=1)))


class HoldExpiryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.fac = facility('expiry')
        cls.room = unit(cls.fac, 'R1')
        cls.citizen = user('citizen-y', role('citizen'))

    def test_expired_hold_is_visible_as_free_and_released(self):
        day = timezone.localdate() + timedelta(days=9)
        lock = InventoryLock.objects.create(
            unit=self.room, date=day, slot='',
            hold_expires_at=timezone.now() - timedelta(minutes=5))
        self.assertTrue(availability.is_free(self.room, day, day + timedelta(days=1)))
        released = availability.release_expired_holds()
        self.assertGreaterEqual(released, 1)
        lock.refresh_from_db()
        self.assertTrue(lock.released)

    def test_payment_window_lapse_cancels_booking_and_releases_locks(self):
        b = booking(self.citizen, self.room, status='awaiting_payment',
                    payment_deadline=timezone.now() - timedelta(hours=1))
        lock = InventoryLock.objects.create(
            unit=self.room, date=b.check_in, slot='', booking=b,
            hold_expires_at=b.payment_deadline)
        count = expire_payment_windows()
        self.assertEqual(count, 1)
        b.refresh_from_db()
        lock.refresh_from_db()
        self.assertEqual(b.status, 'expired')
        self.assertTrue(lock.released)


class FacilityTariffTests(TestCase):
    def test_lowest_tariff_reads_tariffs_through_units(self):
        fac = facility('tariff')
        unit(fac, 'R1', amount='2500.00')
        unit(fac, 'R2', amount='1200.00')
        self.assertEqual(fac.lowest_tariff, Decimal('1200.00'))

    def test_lowest_tariff_ignores_inactive_units(self):
        fac = facility('tariff-inactive')
        unit(fac, 'R1', amount='900.00')
        inactive = unit(fac, 'R2', amount='500.00')
        inactive.is_active = False
        inactive.save(update_fields=['is_active'])
        self.assertEqual(fac.lowest_tariff, Decimal('900.00'))

    def test_lowest_tariff_ignores_non_dakbungalow_assets(self):
        fac = facility('tariff-assets')
        unit(fac, 'R1', amount='900.00')
        unit(fac, 'P1', kind='asset', amount='100.00', asset_category='ponds')
        self.assertEqual(fac.lowest_tariff, Decimal('900.00'))


class LegacyDakbungalowScopeTests(TestCase):
    def setUp(self):
        self.fac = facility('scope')
        self.room = unit(self.fac, 'R1')
        self.pond = unit(self.fac, 'P1', kind='asset', asset_category='ponds')

    def test_available_units_excludes_non_dakbungalow_assets(self):
        start = timezone.localdate() + timedelta(days=3)
        units = availability.available_units(self.fac, start, start + timedelta(days=1))
        self.assertIn(self.room, units)
        self.assertNotIn(self.pond, units)

    def test_facility_calendar_can_scope_to_dakbungalow(self):
        start = timezone.localdate() + timedelta(days=3)
        availability.take_hold(self.pond, [start], '', timezone.now() + timedelta(hours=2))
        day = availability.facility_calendar(self.fac, start, 1,
                                             asset_category='dakbungalow')[0]
        self.assertEqual(day['booked'], 0)
        self.assertEqual(day['free'], 1)

    def test_facility_calendar_without_scope_keeps_all_assets(self):
        start = timezone.localdate() + timedelta(days=3)
        availability.take_hold(self.pond, [start], '', timezone.now() + timedelta(hours=2))
        day = availability.facility_calendar(self.fac, start, 1)[0]
        self.assertEqual(day['booked'], 1)
        self.assertEqual(day['free'], 1)
