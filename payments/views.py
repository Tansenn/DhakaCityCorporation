from __future__ import annotations

from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import perm_required, staff_required
from audit.models import log
from bookings.models import Booking
from core.models import get_bool, get_setting
from core.utils import csv_response, money, paginate, today
from facilities.availability import release_expired_holds
from notifications.services import send
from payments import gateway
from payments.models import Payment, PaymentCallback, Refund


def _payment_for(request, txn_id):
    payment = get_object_or_404(
        Payment.objects.select_related('booking', 'booking__applicant', 'booking__facility',
                                       'booking__unit'), txn_id=txn_id)
    if payment.booking.applicant_id != request.user.pk \
            and not (request.user.is_staff_portal_user and request.user.can('payments.view')):
        raise PermissionDenied('This transaction belongs to another applicant.')
    return payment


def gateway_checkout(request, txn_id):
    payment = _payment_for(request, txn_id)
    booking = payment.booking
    callbacks = payment.callbacks.order_by('-created_at')[:8]
    return render(request, 'payments/gateway.html', {
        'payment': payment, 'booking': booking, 'callbacks': callbacks,
        'provider': get_setting('payment_gateway_provider', 'SSLCommerz / bKash (demo)'),
        'gateway_charge_paid_by_user': get_bool('gateway_charge_paid_by_user', False),
        'page_title': 'Secure payment',
        'is_paid': payment.status == 'success',
    })


@require_POST
def gateway_action(request, txn_id):
    payment = _payment_for(request, txn_id)
    outcome = request.POST.get('outcome', 'pay')
    if outcome == 'duplicate':
        last = payment.callbacks.filter(signature_valid=True).order_by('-created_at').first()
        if last is None:
            messages.error(request, 'No verified callback exists yet to duplicate.')
            return redirect('gateway_checkout', txn_id=txn_id)
        result, message = gateway.handle_callback(last.payload, last.signature)
    elif outcome == 'invalid':
        payload = gateway.callback_payload(payment, 'pay')
        forged = gateway.sign_payload(payload) + 'ff'
        result, message = gateway.handle_callback(payload, forged)
    elif outcome in ('pay', 'fail', 'cancel'):
        channel = (request.POST.get('channel') or 'card')[:24]
        payload = gateway.callback_payload(payment, outcome, channel)
        result, message = gateway.handle_callback(
            payload, gateway.sign_payload(payload))
    else:
        messages.error(request, 'Unknown gateway action.')
        return redirect('gateway_checkout', txn_id=txn_id)

    kind = {'confirmed': 'success', 'duplicate': 'warning', 'rejected': 'error',
            'mismatch': 'error'}.get(result, 'error')
    getattr(messages, kind)(request, f'Gateway callback result: {result}. {message}')
    return redirect('gateway_checkout', txn_id=txn_id)


@perm_required('payments.view')
def payment_list(request):
    rows = Payment.objects.select_related(
        'booking', 'booking__applicant', 'booking__facility').order_by('-initiated_at')
    status = request.GET.get('status', '')
    result = request.GET.get('result', '')
    q = request.GET.get('q', '').strip()
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')
    if status:
        rows = rows.filter(status=status)
    if result == 'duplicate':
        rows = rows.filter(callbacks__result='duplicate').distinct()
    elif result == 'mismatch':
        rows = rows.filter(callbacks__result__in=['mismatch', 'rejected']).distinct()
    elif result == 'failed':
        rows = rows.filter(status__in=['failed', 'cancelled'])
    if q:
        rows = rows.filter(
            Q(txn_id__icontains=q) | Q(booking__reference__icontains=q)
            | Q(receipt_no__icontains=q))
    if date_from:
        rows = rows.filter(initiated_at__date__gte=date_from)
    if date_to:
        rows = rows.filter(initiated_at__date__lte=date_to)

    status_counts = {code: Payment.objects.filter(status=code).count()
                     for code, _label in Payment.STATUS}
    callbacks = {
        'confirmed': PaymentCallback.objects.filter(result='confirmed').count(),
        'duplicate': PaymentCallback.objects.filter(result='duplicate').count(),
        'invalid': PaymentCallback.objects.filter(result='rejected').count(),
        'mismatch': PaymentCallback.objects.filter(result='mismatch').count(),
    }
    demand = Booking.objects.filter(
        status__in=['approved', 'awaiting_payment', 'paid', 'completed']
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    collected = Payment.objects.filter(status='success').aggregate(
        total=Sum('amount'))['total'] or Decimal('0')
    refunded = Refund.objects.filter(status='processed').aggregate(
        total=Sum('amount'))['total'] or Decimal('0')
    return render(request, 'payments/list.html', {
        'page_obj': paginate(request, rows, 25),
        'status_counts': status_counts, 'statuses': Payment.STATUS,
        'callbacks': callbacks,
        'demand': demand, 'collected': collected, 'refunded': refunded,
        'outstanding': demand - collected,
        'status': status, 'result': result, 'q': q,
        'page_title': 'Payments and reconciliation',
    })


@perm_required('payments.view')
def payment_export(request):
    rows = Payment.objects.select_related('booking').order_by('-initiated_at')
    data = [['Transaction', 'Booking', 'Applicant', 'Amount', 'Status', 'Receipt',
             'Initiated', 'Verified']]
    for p in rows[:3000]:
        data.append([p.txn_id, p.booking.reference, p.booking.applicant_name, p.amount,
                     p.get_status_display(), p.receipt_no,
                     p.initiated_at.strftime('%Y-%m-%d %H:%M'),
                     p.verified_at.strftime('%Y-%m-%d %H:%M') if p.verified_at else ''])
    log(request.user, 'export', None, 'Payments exported', module='payments')
    return csv_response('payments.csv', data[0], data[1:])


@perm_required('payments.refund')
def refund_list(request):
    rows = Refund.objects.select_related(
        'booking', 'booking__applicant', 'payment', 'requested_by')
    status = request.GET.get('status', '')
    if status:
        rows = rows.filter(status=status)
    totals = {s[0]: Refund.objects.filter(status=s[0]).count() for s in Refund.STATUS}
    return render(request, 'payments/refunds.html', {
        'page_obj': paginate(request, rows, 25),
        'status': status, 'totals': totals, 'refund_statuses': Refund.STATUS,
        'pending_total': Refund.objects.filter(status='requested').aggregate(
            t=Sum('amount'))['t'] or 0,
        'page_title': 'Refunds',
    })


@require_POST
@perm_required('payments.refund')
def refund_action(request, pk):
    refund = get_object_or_404(
        Refund.objects.select_related('booking', 'booking__applicant'), pk=pk)
    approve = request.POST.get('action') != 'reject'
    ok, message = gateway.process_refund(refund, request.user, approve=approve)
    (messages.success if ok else messages.error)(request, message)
    return redirect('refund_list')


@require_POST
@perm_required('payments.reconcile')
def release_holds(request):
    count = release_expired_holds()
    expired_bookings = gateway.expire_payment_windows()
    messages.success(
        request,
        f'Released {count} expired inventory hold(s). '
        f'Cancelled {expired_bookings} booking(s) whose payment window had lapsed.')
    log(request.user, 'update', None,
        f'Released {count} holds; expired {expired_bookings} bookings', module='payments')
    return redirect(request.POST.get('next') or 'payment_list')
