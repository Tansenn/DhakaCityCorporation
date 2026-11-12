"""Presentation regressions for simulated checkout and payment receipts."""
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table

from core import pdf
from payments.models import Payment

from .factories import booking, facility, role, unit, user


def story_text(items):
    """Inspect the document content without requiring a PDF parser dependency."""
    parts = []
    for item in items:
        if isinstance(item, Paragraph):
            parts.append(item.getPlainText())
        elif isinstance(item, Table):
            for row in item._cellvalues:
                parts.append(story_text(row))
        elif isinstance(item, (list, tuple)):
            parts.append(story_text(item))
        elif isinstance(item, str):
            parts.append(item)
    return '\n'.join(parts)


class ReceiptDesignTests(SimpleTestCase):
    def setUp(self):
        self.booking = SimpleNamespace(
            reference='GZP-DB-RECEIPT',
            applicant=SimpleNamespace(get_full_name=lambda: 'Test Applicant', username='payer'),
            facility=SimpleNamespace(name='Gazipur Dakbungalow'),
            unit=SimpleNamespace(name='Room 101'),
            check_in=date(2026, 12, 10), check_out=date(2026, 12, 12),
            amount=Decimal('5000'), deposit=Decimal('1000'),
            gateway_charge=Decimal('30'), permit_issued_at=None,
        )
        self.payment = SimpleNamespace(
            txn_id='GZP-TXN-RECEIPT', receipt_no='GZP-RCP-RECEIPT',
            amount=Decimal('6030'), verified_at=timezone.now(),
            raw={'channel': 'bkash'}, status='success',
        )

    def render_receipt(self):
        original_build = SimpleDocTemplate.build
        captured = {}

        def capture_and_build(doc, story, *args, **kwargs):
            captured['text'] = story_text(story)
            captured['tables'] = [item for item in story if isinstance(item, Table)]
            captured['signatures'] = [
                row[0] for item in story if isinstance(item, Table)
                for row in item._cellvalues if isinstance(row[0], pdf.SignatureBlock)
            ]
            return original_build(doc, story, *args, **kwargs)

        with patch.object(pdf, 'receipt_signer',
                          return_value=('Farhana Akter', 'Accounts Officer')):
            with patch.object(SimpleDocTemplate, 'build', new=capture_and_build):
                with patch.object(pdf, '_static_image', wraps=pdf._static_image) as images:
                    response = pdf.receipt_pdf(self.booking, self.payment)
        return response, captured, [call.args[0] for call in images.call_args_list]

    def test_branded_pdf_contract_and_tabular_totals(self):
        response, content, images = self.render_receipt()
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response['Content-Disposition'],
                         'attachment; filename="GZP-DB-RECEIPT-receipt.pdf"')
        self.assertTrue(response.content.startswith(b'%PDF-'))
        self.assertIn('img/zp_gazipur_logo.png', images)
        self.assertIn('img/bd_govt_logo.png', images)
        self.assertIn('img/bd_govt_seal.png', images)
        self.assertGreaterEqual(response.content.count(b'/Subtype /Image'), 3)
        text = content['text']
        for value in ('Payment receipt', 'PAID', 'SIMULATED', 'Booking charges',
                      'Security deposit', 'Gateway charge', 'Total paid',
                      'BDT 5,000.00', 'BDT 1,000.00', 'BDT 30.00', 'BDT 6,030.00',
                      'GZP-DB-RECEIPT', 'GZP-TXN-RECEIPT', 'GZP-RCP-RECEIPT',
                      'Payment channel', 'bKash',
                      "Government of the People's Republic of Bangladesh",
                      'RECEIPT NO.', 'PAYMENT DATE', 'STATUS',
                      'Office seal'):
            self.assertIn(value, text)
        self.assertEqual(len(content['signatures']), 1)
        self.assertEqual(content['signatures'][0].name, 'Farhana Akter')
        self.assertEqual(content['signatures'][0].designation, 'Accounts Officer')
        self.assertTrue(any('Total paid' in story_text([table]) and
                            'Booking charges' in story_text([table])
                            for table in content['tables']))
        self.assertTrue(any(command[0] == 'BACKGROUND' and command[-1] == pdf.GREEN
                            for table in content['tables']
                            for command in table._bkgrndcmds))

    def test_prepaid_receipt_does_not_imply_booking_approval(self):
        _, content, _ = self.render_receipt()
        self.assertIn('Pending approval', content['text'])
        self.assertIn('This receipt is not a booking permit.', content['text'])
        self.assertIn('No money was transferred.', content['text'])
        self.assertNotIn('Paid / Confirmed', content['text'])
        self.assertNotIn('Permit issued', content['text'])

    def test_issued_booking_still_requires_separate_permit(self):
        self.booking.permit_issued_at = timezone.now()
        _, content, _ = self.render_receipt()
        self.assertIn('Permit issued separately', content['text'])
        self.assertIn('This receipt is not a booking permit.', content['text'])
        self.assertNotIn('Pending approval', content['text'])

    def test_missing_receipt_metadata_has_safe_fallbacks(self):
        self.payment.receipt_no = ''
        self.payment.raw = {}
        self.payment.verified_at = None
        _, content, _ = self.render_receipt()
        self.assertIn(self.payment.txn_id, content['text'])
        self.assertIn('Not recorded', content['text'])

    def test_user_text_is_not_interpreted_as_reportlab_markup(self):
        self.booking.facility.name = 'A <b>literal</b> & guest house'
        self.booking.applicant.get_full_name = lambda: 'Guest <unclosed'
        response, content, _ = self.render_receipt()
        self.assertTrue(response.content.startswith(b'%PDF-'))
        self.assertIn('A <b>literal</b> & guest house', content['text'])
        self.assertIn('Guest <unclosed', content['text'])

    def test_permit_keeps_three_images_and_left_signature(self):
        self.booking.office_id = ''
        self.booking.national_id = ''
        self.booking.permit_no = 'GZP-PRM-RECEIPT'
        self.booking.get_category_display = lambda: 'Citizen'
        self.booking.facility.location = 'Gazipur'
        self.booking.guests = 2
        self.booking.purpose = 'Test visit'
        self.booking.payment_txn_id = self.payment.txn_id
        original_build = SimpleDocTemplate.build
        signature_rows = []

        def capture_and_build(doc, story, *args, **kwargs):
            for item in story:
                if isinstance(item, Table):
                    signature_rows.extend(list(row) for row in item._cellvalues
                                          if isinstance(row[0], pdf.SignatureBlock))
            return original_build(doc, story, *args, **kwargs)

        with patch.object(pdf, 'permit_approver', return_value=None):
            with patch.object(SimpleDocTemplate, 'build', new=capture_and_build):
                response = pdf.permit_pdf(self.booking, 'https://example.test/verify/token/')
        self.assertTrue(response.content.startswith(b'%PDF-'))
        # Transparent logos add soft-mask image objects, not extra visible images.
        visible_images = (response.content.count(b'/Subtype /Image')
                          - response.content.count(b'/SMask'))
        self.assertEqual(visible_images, 3)
        self.assertEqual(len(signature_rows), 1)
        self.assertIsInstance(signature_rows[0][0], pdf.SignatureBlock)


class CheckoutPresentationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.citizen = user('receipt-payer', role('citizen'))
        cls.room = unit(facility('receipt-design'))

    def setUp(self):
        self.booking = booking(self.citizen, self.room, status='submitted')
        self.payment = Payment.objects.create(
            booking=self.booking, txn_id='GZP-TXN-DESIGN', amount=self.booking.total)
        self.client.force_login(self.citizen)
        session = self.client.session
        session['gzp_lang'] = 'en'
        session.save()

    def checkout(self):
        return self.client.get(f'/pay/{self.payment.txn_id}/')

    def test_prepaid_pending_checkout_has_receipt_not_permit(self):
        self.payment.status = 'success'
        self.payment.verified_at = timezone.now()
        self.payment.save()
        response = self.checkout()
        self.assertContains(response, 'Payment received')
        self.assertContains(response, 'Pending approval')
        self.assertContains(response, f'/bookings/{self.booking.pk}/receipt.pdf')
        self.assertContains(response, f'/bookings/{self.booking.pk}/')
        self.assertContains(response, 'href="/citizen/"')
        self.assertContains(response, 'href="/user/"')
        self.assertNotContains(response, '/permit.pdf')
        self.assertNotContains(response, 'id="gw-form"')

    def test_permit_link_requires_actual_issue_timestamp(self):
        self.payment.status = 'success'
        self.payment.save()
        self.booking.permit_issued_at = timezone.now()
        self.booking.save(update_fields=['permit_issued_at'])
        response = self.checkout()
        self.assertContains(response, f'/bookings/{self.booking.pk}/permit.pdf')
        self.assertNotContains(response, 'Pending approval')

    def test_simulated_channels_and_callback_controls_remain_available(self):
        response = self.checkout()
        self.assertContains(response, 'Simulated payment · No money is transferred')
        self.assertContains(response, f'action="/pay/{self.payment.txn_id}/callback/"', count=5)
        for outcome in ('pay', 'fail', 'cancel', 'duplicate', 'invalid'):
            self.assertContains(response, f'name="outcome" value="{outcome}"')
        for channel in ('card', 'bkash', 'nagad', 'rocket', 'bank', 'netbanking'):
            self.assertContains(response, f'value="{channel}"')
        for brand in ('bkash', 'nagad', 'rocket', 'ekpay'):
            self.assertContains(response, f'img/payment-{brand}.png')
        self.assertContains(response, f'/bookings/{self.booking.pk}/qr.png')
        self.assertContains(response, 'role="tablist"')
        self.assertContains(response, 'aria-selected="true"')
        for removed in ('autocomplete="cc-', 'type="password"', 'gw-clock',
                        'setInterval', 'PCI DSS', 'Verified by Visa', 'Powered by',
                        'Remember this card', 'confirmation SMS'):
            self.assertNotContains(response, removed)

    def held_payment(self, index):
        from core.utils import daterange_days
        from facilities.availability import take_hold

        reservation = booking(
            self.citizen, self.room, status='awaiting_payment', start_days=10 + index * 3)
        take_hold(self.room, list(daterange_days(reservation.check_in, reservation.check_out)),
                  '', timezone.now() + timedelta(hours=2), booking=reservation)
        return Payment.objects.create(
            booking=reservation, txn_id=f'GZP-TXN-CHANNEL-{index}', amount=reservation.total)

    def test_each_channel_posts_to_existing_callback_and_produces_receipt(self):
        for index, channel in enumerate(('card', 'bkash', 'nagad', 'rocket', 'bank',
                                         'netbanking', 'ekpay')):
            with self.subTest(channel=channel):
                payment = self.held_payment(index)
                response = self.client.post(f'/pay/{payment.txn_id}/callback/',
                                            {'outcome': 'pay', 'channel': channel})
                self.assertRedirects(response, f'/pay/{payment.txn_id}/')
                payment.refresh_from_db()
                self.assertEqual(payment.status, 'success')
                self.assertEqual(payment.raw['channel'], channel)
                receipt = self.client.get(f'/bookings/{payment.booking_id}/receipt.pdf')
                self.assertEqual(receipt['Content-Type'], 'application/pdf')
                self.assertTrue(receipt.content.startswith(b'%PDF-'))

    def test_failure_cancel_duplicate_and_forged_posts_keep_their_contract(self):
        payment = self.held_payment(0)
        for outcome, result in (('fail', 'failed'), ('cancel', 'cancelled'),
                                ('pay', 'confirmed'), ('duplicate', 'duplicate'),
                                ('invalid', 'rejected')):
            with self.subTest(outcome=outcome):
                response = self.client.post(f'/pay/{payment.txn_id}/callback/',
                                            {'outcome': outcome, 'channel': 'nagad'})
                self.assertEqual(response.status_code, 302)
                self.assertEqual(payment.callbacks.order_by('-created_at', '-pk').first().result,
                                 result)

    def test_failed_and_cancelled_transactions_keep_retry_and_test_controls(self):
        for status in ('failed', 'cancelled'):
            with self.subTest(status=status):
                self.payment.status = status
                self.payment.save(update_fields=['status'])
                response = self.checkout()
                self.assertContains(response, 'id="gw-form"')
                self.assertContains(response, 'name="outcome" value="pay"')
                self.assertContains(response, 'name="outcome" value="duplicate"')
