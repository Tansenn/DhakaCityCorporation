from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from bookings.journey import build_journey
from facilities.availability import release_booking_locks, take_hold
from notifications.models import Notification
from payments import gateway
from payments.models import Payment, PaymentCallback, Refund
from workflow import engine

from .factories import booking, booking_template, facility, role, unit, user


class UserPaymentLifecycleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.template = booking_template()
        cls.applicant = user('direct-payer', role('citizen'))
        cls.desk = user('direct-desk', role('bookingdesk'))
        cls.eo = user('direct-eo', role('eo'))
        cls.ceo = user('direct-ceo', role('ceo'))
        cls.room = unit(facility('direct-payments'), 'R1')

    def setUp(self):
        self.booking = booking(
            self.applicant, self.room,
            hold_expires_at=timezone.now() + timedelta(hours=48))
        self.booking.payment_flow = 'direct'
        self.booking.save()
        take_hold(
            self.room,
            [self.booking.check_in, self.booking.check_in + timedelta(days=1)],
            '', self.booking.hold_expires_at, booking=self.booking)
        self.instance = engine.start(
            self.template, self.booking, {'unit_kind': 'room', 'amount': 5500},
            self.applicant)

    def callback(self, payment, outcome='pay', **overrides):
        payload = gateway.callback_payload(payment, outcome)
        payload.update(overrides)
        return gateway.handle_callback(payload, gateway.sign_payload(payload))

    def collect(self):
        payment = gateway.start_payment(self.booking)
        result, _ = self.callback(payment)
        self.assertEqual(result, 'confirmed')
        payment.refresh_from_db()
        self.booking.refresh_from_db()
        return payment

    def decide(self, actor, decision, comments='Checked'):
        ok, message = engine.decide(
            self.instance.tasks.get(status='pending'), actor, decision, comments)
        self.assertTrue(ok, message)
        self.instance.refresh_from_db()
        self.booking.refresh_from_db()

    def test_direct_payment_is_verified_without_approval_or_permit(self):
        payment = self.collect()
        self.assertTrue(payment.is_settled)
        self.assertTrue(payment.signature)
        self.assertTrue(payment.receipt_no)
        self.assertEqual(self.booking.status, 'submitted')
        self.assertIsNone(self.booking.approved_at)
        self.assertIsNone(self.booking.permit_issued_at)
        self.assertFalse(self.booking.permit_no)
        self.assertIsNone(self.booking.hold_expires_at)
        self.assertIsNone(self.booking.payment_deadline)
        self.assertEqual(self.booking.locks.filter(
            released=False, hold_expires_at__isnull=True).count(), 2)
        self.assertFalse(self.booking.can_pay)
        self.assertEqual(Notification.objects.filter(template_code='payment_receipt').count(), 1)
        self.assertFalse(Notification.objects.filter(template_code='permit_ready').exists())
        self.assertFalse(self.booking.status_changes.filter(to_status='paid').exists())

    def test_all_direct_pending_statuses_can_pay_with_active_inventory(self):
        for status in ('submitted', 'under_review', 'recommended', 'clarification', 'approved'):
            with self.subTest(status=status):
                self.booking.status = status
                self.booking.save(update_fields=['status'])
                self.assertTrue(self.booking.can_pay)

    def test_terminal_statuses_cannot_pay(self):
        for status in ('rejected', 'cancelled', 'expired', 'paid', 'completed'):
            with self.subTest(status=status):
                self.booking.status = status
                self.booking.save(update_fields=['status'])
                self.assertFalse(self.booking.can_pay)
                payment = Payment.objects.create(
                    booking=self.booking, txn_id=f'terminal-{status}', amount=self.booking.total)
                self.assertEqual(self.callback(payment)[0], 'mismatch')
                payment.refresh_from_db()
                self.assertFalse(payment.is_settled)

    def test_default_approval_first_cannot_collect_early(self):
        self.booking.payment_flow = 'approval_first'
        self.booking.save()
        self.assertFalse(self.booking.can_pay)
        payment = Payment.objects.create(
            booking=self.booking, txn_id='early-approval-first', amount=self.booking.total)
        self.assertEqual(self.callback(payment)[0], 'mismatch')
        self.assertIsNone(self.booking.payment)

    def test_approval_first_final_approval_then_payment_still_issues_permit(self):
        self.booking.payment_flow = 'approval_first'
        self.booking.save()
        self.decide(self.desk, 'forward')
        self.decide(self.eo, 'approve')
        self.assertEqual(self.booking.status, 'awaiting_payment')
        self.assertIsNotNone(self.booking.payment_deadline)
        self.assertTrue(self.booking.can_pay)
        self.collect()
        self.assertEqual(self.booking.status, 'paid')
        self.assertTrue(self.booking.permit_no)

    def test_prepaid_final_approval_issues_exactly_one_permit(self):
        self.collect()
        self.decide(self.desk, 'forward')
        self.assertEqual(self.booking.status, 'under_review')
        self.assertIsNone(self.booking.hold_expires_at)
        self.decide(self.eo, 'approve')
        self.assertEqual(self.booking.status, 'paid')
        self.assertIsNotNone(self.booking.approved_at)
        self.assertTrue(self.booking.permit_no)
        self.assertIsNotNone(self.booking.permit_issued_at)
        self.assertFalse(self.booking.status_changes.filter(to_status='awaiting_payment').exists())
        issued_at = self.booking.permit_issued_at
        self.booking.on_workflow_decision('approve', self.instance)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.permit_issued_at, issued_at)
        self.assertEqual(self.booking.status_changes.filter(to_status='paid').count(), 1)
        self.assertEqual(Notification.objects.filter(template_code='permit_ready').count(), 1)

    def test_intermediate_approval_does_not_expire_prepaid_inventory(self):
        self.instance.payload['amount'] = 25000
        self.instance.save(update_fields=['payload'])
        self.collect()
        self.decide(self.desk, 'forward')
        self.decide(self.eo, 'recommend')
        self.assertEqual(self.booking.status, 'recommended')
        self.assertIsNone(self.booking.hold_expires_at)
        self.assertFalse(self.booking.locks.filter(hold_expires_at__isnull=False).exists())
        self.assertFalse(self.booking.permit_no)
        self.decide(self.ceo, 'approve')
        self.assertEqual(self.booking.status, 'paid')

    def test_prepaid_correction_preserves_payment_and_nonexpiring_hold(self):
        payment = self.collect()
        self.decide(self.desk, 'correct', 'Please attach evidence')
        self.assertEqual(self.booking.status, 'clarification')
        self.assertEqual(self.booking.payment, payment)
        self.assertIsNone(self.booking.hold_expires_at)
        self.assertFalse(self.booking.can_pay)
        journey = build_journey(self.booking)
        self.assertIn('Payment received', journey['instruction'])
        self.assertIn('correction', journey['instruction'])

    def test_multiple_initiated_transactions_collect_only_once(self):
        first = gateway.start_payment(self.booking)
        second = Payment.objects.create(
            booking=self.booking, txn_id='parallel-checkout', amount=self.booking.total)
        self.assertEqual(self.callback(first)[0], 'confirmed')
        self.assertEqual(self.callback(second)[0], 'duplicate')
        self.assertEqual(self.callback(first)[0], 'duplicate')
        second.refresh_from_db()
        self.assertEqual(second.status, 'initiated')
        self.assertEqual(self.booking.payments.filter(status='success').count(), 1)
        self.assertEqual(PaymentCallback.objects.filter(result='confirmed').count(), 1)
        self.assertEqual(Notification.objects.filter(template_code='payment_receipt').count(), 1)

    def test_failed_direct_payment_can_retry(self):
        first = gateway.start_payment(self.booking)
        self.assertEqual(self.callback(first, 'fail')[0], 'failed')
        self.booking.refresh_from_db()
        self.assertTrue(self.booking.can_pay)
        self.collect()
        self.assertEqual(self.booking.status, 'submitted')

    def test_prepaid_rejection_requests_one_full_refund_and_releases_inventory(self):
        payment = self.collect()
        self.decide(self.desk, 'reject', 'Application not eligible')
        refund = Refund.objects.get(booking=self.booking)
        self.assertEqual(refund.payment, payment)
        self.assertEqual(refund.status, 'requested')
        self.assertEqual(refund.amount, Decimal('5500.00'))
        self.assertEqual(refund.percent, Decimal('100.00'))
        self.assertIn('Application not eligible', refund.reason)
        self.assertEqual(self.booking.status, 'rejected')
        self.assertEqual(self.booking.refund_status, 'requested')
        self.assertEqual(self.booking.refund_amount, payment.amount)
        self.assertEqual(self.booking.refund_percent, Decimal('100.00'))
        self.assertIsNotNone(self.booking.refund_requested_at)
        self.assertFalse(self.booking.locks.filter(released=False).exists())
        self.assertIsNone(self.booking.payment_deadline)
        self.assertFalse(self.booking.permit_no)
        self.booking.on_workflow_decision('reject', self.instance)
        self.assertEqual(Refund.objects.filter(booking=self.booking).count(), 1)
        payment.refresh_from_db()
        self.assertTrue(payment.is_settled)

    def test_unpaid_rejection_does_not_request_a_refund(self):
        self.decide(self.desk, 'reject')
        self.assertFalse(self.booking.refunds.exists())
        self.assertFalse(self.booking.locks.filter(released=False).exists())

    def test_double_cancel_of_prepaid_booking_opens_one_refund(self):
        from bookings.views import cancel_booking
        payment = self.collect()
        ok, refund = cancel_booking(self.booking, self.applicant, 'Changed plans')
        self.assertTrue(ok)
        self.assertEqual(refund.payment, payment)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'cancelled')
        self.assertEqual(self.booking.refund_status, 'requested')
        self.assertFalse(self.booking.locks.filter(released=False).exists())
        ok, message = cancel_booking(self.booking, self.applicant, 'Changed plans')
        self.assertFalse(ok)
        self.assertEqual(Refund.objects.filter(booking=self.booking).count(), 1)

    def test_expired_booking_hold_cannot_collect(self):
        payment = gateway.start_payment(self.booking)
        self.booking.hold_expires_at = timezone.now() - timedelta(seconds=1)
        self.booking.save(update_fields=['hold_expires_at'])
        self.assertFalse(self.booking.can_pay)
        self.assertEqual(self.callback(payment)[0], 'mismatch')
        self.assertIsNone(self.booking.payment)

    def test_expired_inventory_cannot_collect_even_with_future_booking_hold(self):
        payment = gateway.start_payment(self.booking)
        self.booking.locks.update(hold_expires_at=timezone.now() - timedelta(seconds=1))
        self.assertFalse(self.booking.can_pay)
        self.assertEqual(self.callback(payment)[0], 'mismatch')
        self.assertFalse(self.booking.locks.filter(hold_expires_at__isnull=True).exists())

    def test_released_and_reassigned_inventory_cannot_collect(self):
        payment = gateway.start_payment(self.booking)
        release_booking_locks(self.booking)
        other = booking(self.applicant, self.room)
        take_hold(self.room, [other.check_in, other.check_in + timedelta(days=1)],
                  '', None, booking=other)
        self.assertFalse(self.booking.can_pay)
        self.assertEqual(self.callback(payment)[0], 'mismatch')
        self.assertIsNone(self.booking.payment)
        self.assertEqual(other.locks.filter(released=False).count(), 2)
        self.assertFalse(self.booking.locks.filter(released=False).exists())

    def test_missing_one_night_cannot_collect(self):
        payment = gateway.start_payment(self.booking)
        self.booking.locks.filter(date=self.booking.check_in).update(released=True)
        self.assertFalse(self.booking.can_pay)
        self.assertEqual(self.callback(payment)[0], 'mismatch')

    def test_direct_booking_without_inventory_cannot_collect(self):
        payment = gateway.start_payment(self.booking)
        self.booking.locks.all().delete()
        self.assertFalse(self.booking.can_pay)
        self.assertEqual(self.callback(payment)[0], 'mismatch')

    def test_payment_deadline_is_enforced_for_both_flows(self):
        payment = gateway.start_payment(self.booking)
        for flow in ('direct', 'approval_first'):
            with self.subTest(flow=flow):
                self.booking.payment_flow = flow
                self.booking.status = 'awaiting_payment'
                self.booking.payment_deadline = timezone.now() - timedelta(seconds=1)
                self.booking.save()
                self.assertFalse(self.booking.can_pay)
                self.assertEqual(self.callback(payment)[0], 'mismatch')
        self.assertIsNone(self.booking.payment)

    def test_final_approval_never_confirms_prepaid_released_inventory(self):
        self.collect()
        release_booking_locks(self.booking)
        self.decide(self.desk, 'forward')
        self.decide(self.eo, 'approve')
        self.assertNotEqual(self.booking.status, 'paid')
        self.assertFalse(self.booking.permit_no)
        self.assertFalse(self.booking.locks.filter(released=False).exists())

    def test_unverified_success_is_not_a_received_payment(self):
        Payment.objects.create(booking=self.booking, txn_id='unverified-success',
                               amount=self.booking.total, status='success')
        self.assertIsNone(self.booking.payment)
        self.assertTrue(self.booking.can_pay)
        self.assertFalse(any(stage['key'] == 'payment' and stage['state'] == 'done'
                             for stage in build_journey(self.booking)['stages']))

    def test_callback_cannot_confirm_an_outdated_demand(self):
        payment = gateway.start_payment(self.booking)
        self.booking.status = 'awaiting_payment'
        self.booking.total += Decimal('100.00')
        self.booking.save(update_fields=['status', 'total'])
        self.assertEqual(self.callback(payment)[0], 'mismatch')
        self.assertIsNone(self.booking.payment)

    def test_approval_status_does_not_bypass_running_workflow(self):
        self.booking.status = 'approved'
        self.booking.save(update_fields=['status'])
        self.collect()
        self.assertEqual(self.booking.status, 'approved')
        self.assertFalse(self.booking.permit_no)
        self.assertFalse(self.booking.confirm_paid())

    def test_prepaid_journey_does_not_fabricate_approval_or_permit(self):
        self.collect()
        journey = build_journey(self.booking)
        stages = {stage['key']: stage for stage in journey['stages']}
        self.assertEqual(stages['payment']['state'], 'done')
        self.assertEqual(stages['permit']['state'], 'waiting')
        self.assertIn('Payment received', journey['instruction'])
        self.assertIn('pending', journey['instruction'])
        workflow_stages = [stage for stage in journey['stages'] if stage['key'].startswith('step-')]
        self.assertEqual([stage['role_code'] for stage in workflow_stages], ['bookingdesk', 'eo'])
        self.assertEqual([stage['state'] for stage in workflow_stages], ['current', 'waiting'])
        self.assertEqual(journey['current']['role_code'], 'bookingdesk')
        self.assertFalse(Notification.objects.filter(url__endswith='/permit.pdf').exists())
