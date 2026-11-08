from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from payments import gateway
from payments.models import Payment, PaymentCallback

from .factories import booking, facility, role, unit, user


class PaymentCallbackTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.fac = facility('gateway')
        cls.room = unit(cls.fac, 'R1')
        cls.citizen = user('payer', role('citizen'))

    def setUp(self):
        self.booking = booking(
            self.citizen, self.room, status='awaiting_payment',
            payment_deadline=timezone.now() + timedelta(hours=5),
            amount='5500.00')
        self.payment = gateway.start_payment(self.booking)

    def signed(self, outcome='pay', **overrides):
        payload = gateway.callback_payload(self.payment, outcome)
        payload.update(overrides)
        return payload, gateway.sign_payload(payload)

    def test_valid_callback_confirms_payment_and_issues_permit(self):
        payload, signature = self.signed('pay')
        result, _ = gateway.handle_callback(payload, signature)
        self.assertEqual(result, 'confirmed')
        self.payment.refresh_from_db()
        self.booking.refresh_from_db()
        self.assertEqual(self.payment.status, 'success')
        self.assertEqual(self.booking.status, 'paid')
        self.assertTrue(self.booking.permit_no)
        self.assertTrue(self.booking.permit_issued_at)
        self.assertEqual(
            PaymentCallback.objects.filter(payment=self.payment, result='confirmed').count(),
            1)

    def test_replayed_callback_is_recorded_as_duplicate(self):
        payload, signature = self.signed('pay')
        gateway.handle_callback(payload, signature)
        replay_payload, replay_signature = self.signed('pay')
        result, message = gateway.handle_callback(replay_payload, replay_signature)
        self.assertEqual(result, 'duplicate')
        self.assertIn('already confirmed', message)
        self.assertEqual(
            PaymentCallback.objects.filter(payment=self.payment, result='duplicate').count(),
            1)

    def test_forged_signature_is_rejected_and_payment_stays_pending(self):
        payload, signature = self.signed('pay')
        result, _ = gateway.handle_callback(payload, signature + 'ff')
        self.assertEqual(result, 'rejected')
        self.payment.refresh_from_db()
        self.booking.refresh_from_db()
        self.assertEqual(self.payment.status, 'initiated')
        self.assertEqual(self.booking.status, 'awaiting_payment')
        self.assertFalse(self.booking.permit_no)

    def test_tampered_amount_is_recorded_as_mismatch(self):
        payload, signature = self.signed('pay', amount='1.00')
        result, _ = gateway.handle_callback(payload, signature)
        self.assertEqual(result, 'mismatch')
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'initiated')

    def test_unknown_transaction_is_stored_and_rejected(self):
        payload = {'txn_id': 'GZP-TXN-UNKNOWN', 'amount': '10.00',
                   'booking': 'GZP-DB-UNKNOWN', 'status': 'SUCCESS'}
        result, _ = gateway.handle_callback(payload, gateway.sign_payload(payload))
        self.assertEqual(result, 'mismatch')
        record = PaymentCallback.objects.get(txn_id='GZP-TXN-UNKNOWN')
        self.assertIsNone(record.payment)

    def test_failed_callback_marks_payment_failed_and_can_be_retried(self):
        payload, signature = self.signed('fail')
        result, _ = gateway.handle_callback(payload, signature)
        self.assertEqual(result, 'failed')
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'failed')
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'awaiting_payment')
        retry = gateway.start_payment(self.booking)
        payload, signature = gateway.callback_payload(retry, 'pay'), None
        signature = gateway.sign_payload(payload)
        self.assertEqual(gateway.handle_callback(payload, signature)[0], 'confirmed')

    def test_signature_is_hmac_and_changes_with_payload(self):
        payload, signature = self.signed('pay')
        self.assertTrue(gateway.verify_signature(payload, signature))
        payload['amount'] = '0.01'
        self.assertFalse(gateway.verify_signature(payload, signature))

    def test_payment_page_only_serves_its_owner(self):
        other = user('other-payer', role('citizen'))
        self.client.force_login(other)
        response = self.client.get(f'/pay/{self.payment.txn_id}/')
        self.assertEqual(response.status_code, 403)
        self.client.force_login(self.citizen)
        response = self.client.get(f'/pay/{self.payment.txn_id}/')
        self.assertEqual(response.status_code, 200)
