"""Simulated payment gateway with real server-side callback verification.

The demo gateway page behaves like a hosted checkout: it produces a callback
that is HMAC-signed with a shared secret. The application confirms a payment
only after verifying that signature. Duplicate, mismatched and forged callbacks
are recorded and rejected.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from audit.models import log
from bookings.models import Booking, BookingStatusChange
from core.models import get_setting
from core.utils import money
from notifications.services import send
from payments.models import Payment, PaymentCallback, Refund

GATEWAY_NAME = 'Demo gateway'


def sign_payload(payload):
    body = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode()
    return hmac.new(
        settings.PAYMENT_GATEWAY_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()


def verify_signature(payload, signature):
    if not signature:
        return False
    expected = sign_payload(payload)
    return hmac.compare_digest(expected, str(signature))


def new_txn_id():
    return f'GZP-TXN-{timezone.now():%Y%m%d%H%M%S}-{secrets.token_hex(3).upper()}'


def start_payment(booking):
    """Open a gateway transaction for an approved booking."""
    payment = Payment.objects.create(
        booking=booking,
        txn_id=new_txn_id(),
        gateway=get_setting('payment_gateway_provider', GATEWAY_NAME),
        amount=booking.total,
        raw={'booking': booking.reference, 'amount': str(booking.total)},
    )
    log(booking.applicant, 'payment', booking,
        f'Gateway transaction {payment.txn_id} opened for {money(payment.amount)}',
        module='payments')
    return payment


def callback_payload(payment, outcome):
    """Build the payload a hosted gateway would POST back."""
    status = {'pay': 'SUCCESS', 'fail': 'FAILED', 'cancel': 'CANCELLED'}.get(
        outcome, outcome.upper())
    return {
        'txn_id': payment.txn_id,
        'booking': payment.booking.reference,
        'amount': str(payment.amount),
        'currency': 'BDT',
        'status': status,
        'store_amount': str(payment.amount),
        'nonce': secrets.token_hex(8),
        'gateway_time': timezone.now().isoformat(timespec='seconds'),
    }


@transaction.atomic
def handle_callback(payload, signature):
    """Verify a signed gateway callback and apply it. Returns (result, message)."""
    payload = dict(payload or {})
    txn_id = str(payload.get('txn_id') or '')
    payment = Payment.objects.select_for_update().filter(txn_id=txn_id).first()
    valid = verify_signature(payload, signature)

    record = PaymentCallback.objects.create(
        payment=payment, txn_id=txn_id, signature=str(signature or '')[:128],
        signature_valid=valid, kind=str(payload.get('status') or ''),
        payload=payload,
    )
    if payment is None:
        record.result = 'mismatch'
        record.save(update_fields=['result'])
        log(None, 'payment', None,
            f'Callback rejected: unknown transaction {txn_id}', module='payments')
        return 'mismatch', 'Unknown transaction reference.'

    if not valid:
        record.result = 'rejected'
        record.save(update_fields=['result'])
        log(None, 'payment', payment,
            f'Callback rejected: invalid signature for {txn_id}', module='payments')
        return 'rejected', 'Invalid signature. The callback was rejected.'

    booking = payment.booking
    try:
        amount = Decimal(str(payload.get('amount')))
    except (InvalidOperation, TypeError):
        amount = Decimal('-1')
    if amount != payment.amount or payload.get('booking') not in (None, booking.reference):
        record.result = 'mismatch'
        record.save(update_fields=['result'])
        log(None, 'payment', payment,
            f'Callback mismatch for {txn_id}: amount {payload.get("amount")} vs {payment.amount}',
            module='payments')
        return 'mismatch', 'Amount or booking reference does not match the demand.'

    if payment.status == 'success':
        record.result = 'duplicate'
        record.save(update_fields=['result'])
        log(None, 'payment', payment,
            f'Duplicate callback ignored for {txn_id}', module='payments')
        return 'duplicate', 'This transaction was already confirmed. Duplicate callback ignored.'

    if booking.status != 'awaiting_payment':
        record.result = 'mismatch'
        record.save(update_fields=['result'])
        return 'mismatch', 'The booking is no longer awaiting payment.'

    status = str(payload.get('status') or '').upper()
    if status == 'SUCCESS':
        payment.status = 'success'
        payment.verified_at = timezone.now()
        payment.receipt_no = f'GZP-RCP-{booking.reference.split("-")[-1]}'
        payment.signature = str(signature)
        payment.raw = payload
        payment.save()
        record.result = 'confirmed'
        record.save(update_fields=['result'])

        booking.status = 'paid'
        booking.hold_expires_at = None
        booking.payment_deadline = None
        booking.permit_no = booking.reference.replace('GZP-DB', 'GZP-PRM')
        booking.permit_issued_at = timezone.now()
        booking.save(update_fields=['status', 'hold_expires_at', 'payment_deadline',
                                    'permit_no', 'permit_issued_at', 'updated_at'])
        BookingStatusChange.objects.create(
            booking=booking, from_status='awaiting_payment', to_status='paid',
            comment=f'Payment {payment.txn_id} verified by gateway callback',
        )
        booking.locks.filter(released=False).update(hold_expires_at=None)

        send(booking.applicant, 'payment_receipt', {
            'reference': booking.reference,
            'subject': f'Payment received for {booking.reference}',
            'message': f'{money(payment.amount)} received. Receipt {payment.receipt_no}.',
            'amount': money(payment.amount),
            'receipt': payment.receipt_no,
        }, url=f'/bookings/{booking.pk}/', channels=['inapp', 'email', 'sms'])
        send(booking.applicant, 'permit_ready', {
            'reference': booking.reference,
            'subject': f'Your booking permit is ready - {booking.reference}',
            'message': 'Download the permit from your application page.',
        }, url=f'/bookings/{booking.pk}/permit.pdf', channels=['inapp', 'email'])
        log(booking.applicant, 'payment', booking,
            f'Payment confirmed {payment.txn_id} {money(payment.amount)}', module='payments')
        return 'confirmed', 'Payment verified and booking confirmed.'

    if status in ('FAILED', 'CANCELLED'):
        payment.status = 'failed' if status == 'FAILED' else 'cancelled'
        payment.raw = payload
        payment.save(update_fields=['status', 'raw'])
        record.result = 'failed' if status == 'FAILED' else 'cancelled'
        record.save(update_fields=['result'])
        send(booking.applicant, 'status_update', {
            'reference': booking.reference,
            'subject': f'Payment {status.lower()} for {booking.reference}',
            'message': 'You can retry payment from your application page while the payment window is open.',
        }, url=f'/bookings/{booking.pk}/', channels=['inapp', 'email'])
        log(booking.applicant, 'payment', booking,
            f'Gateway reported {status} for {payment.txn_id}', module='payments')
        return record.result, 'The gateway reported that the payment did not complete.'

    record.result = 'mismatch'
    record.save(update_fields=['result'])
    return 'mismatch', 'Unsupported gateway status.'


@transaction.atomic
def process_refund(refund, user, approve=True):
    """Simulated gateway refund. No money moves; the reference is recorded."""
    booking = refund.booking
    if refund.status == 'processed':
        return False, 'This refund has already been processed.'
    payment = refund.payment or Payment.objects.filter(
        booking=booking, status__in=('success', 'refunded')).first()
    if not approve:
        refund.status = 'rejected'
        refund.processed_by = user
        refund.processed_at = timezone.now()
        refund.save()
        booking.refund_status = 'rejected'
        booking.save(update_fields=['refund_status'])
        log(user, 'update', booking,
            f'Refund rejected for {booking.reference}', module='payments')
        return True, 'Refund request rejected.'

    refund.status = 'processed'
    refund.processed_by = user
    refund.processed_at = timezone.now()
    refund.gateway_ref = f'GZP-RFD-{secrets.token_hex(4).upper()}'
    refund.save()
    if payment:
        payment.status = 'refunded'
        payment.refunded_amount = (payment.refunded_amount or Decimal('0')) + refund.amount
        payment.refunded_at = timezone.now()
        payment.save(update_fields=['status', 'refunded_amount', 'refunded_at'])
    booking.refund_status = 'processed'
    booking.status = 'cancelled'
    booking.cancelled_at = timezone.now()
    booking.cancellation_reason = f'Refund processed ({refund.percent}%)'
    booking.save(update_fields=['refund_status', 'status', 'cancelled_at',
                                'cancellation_reason', 'updated_at'])
    from facilities.availability import release_booking_locks

    release_booking_locks(booking)
    BookingStatusChange.objects.create(
        booking=booking, from_status='paid', to_status='cancelled',
        actor=user, comment=f'Refund {refund.gateway_ref} processed for {money(refund.amount)}',
    )
    send(booking.applicant, 'status_update', {
        'reference': booking.reference,
        'subject': f'Refund processed for {booking.reference}',
        'message': f'{money(refund.amount)} ({refund.percent}%) has been refunded in the demo gateway.',
    }, url=f'/bookings/{booking.pk}/', channels=['inapp', 'email', 'sms'])
    log(user, 'payment', booking,
        f'Refund {refund.gateway_ref} {money(refund.amount)} processed', module='payments')
    return True, f'Refund {refund.gateway_ref} processed. The booking is cancelled.'


def expire_payment_windows():
    """Cancel bookings whose payment window lapsed and release their inventory."""
    from facilities.availability import release_booking_locks

    now = timezone.now()
    expired = Booking.objects.filter(
        status='awaiting_payment', payment_deadline__isnull=False,
        payment_deadline__lt=now)
    count = 0
    for booking in expired:
        BookingStatusChange.objects.create(
            booking=booking, from_status='awaiting_payment', to_status='expired',
            comment='Payment window expired; inventory released',
        )
        booking.status = 'expired'
        booking.save(update_fields=['status', 'updated_at'])
        release_booking_locks(booking)
        booking.hold_expires_at = None
        booking.save(update_fields=['hold_expires_at'])
        send(booking.applicant, 'status_update', {
            'reference': booking.reference,
            'subject': f'Payment window expired - {booking.reference}',
            'message': 'The payment window closed and the hold was released. Please apply again if you still need the facility.',
        }, url=f'/bookings/{booking.pk}/', channels=['inapp', 'email'])
        count += 1
    return count
