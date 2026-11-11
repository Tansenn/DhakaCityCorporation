from __future__ import annotations

import csv
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import citizen_required, perm_required, staff_required
from audit.models import log
from bookings.forms import ApplyForm, DetailsForm
from bookings.journey import build_journey
from bookings.models import (
    Booking,
    BookingDocument,
    BookingMessage,
    BookingStatusChange,
    STATUSES,
)
from core.assets import asset_status
from core.pdf import permit_pdf, receipt_pdf
from core.utils import csv_response, daterange_days, money, paginate, parse_date, today, validate_upload
from facilities import availability
from facilities.availability import (
    HALL_SLOTS,
    active_lock_filter,
    is_free,
    quote,
    release_booking_locks,
    take_hold,
)
from facilities.models import Facility, InventoryLock, Unit
from notifications.services import send
from payments.gateway import start_payment
from payments.models import Refund
from workflow import engine
from workflow.models import WorkflowInstance, WorkflowTemplate, WorkflowTask

REQUIRED_DOCS = {
    'government': 'NID or government office / service ID (sample)',
    'citizen': 'National ID - NID, 10 to 17 digits (sample)',
    'organization': 'National ID of the representative and a letter on letterhead (sample)',
}


# --------------------------------------------------------------------- helpers
def _staff_booking_queryset(user):
    qs = Booking.objects.select_related('facility', 'unit', 'applicant')
    if user.role and user.role.code == 'reception' and user.facility_id:
        qs = qs.filter(facility_id=user.facility_id)
    return qs


def _get_booking(request, pk, allow_staff=True):
    booking = get_object_or_404(
        Booking.objects.select_related('facility', 'unit', 'applicant'), pk=pk)
    if booking.applicant_id == request.user.pk:
        return booking, False
    if allow_staff and request.user.is_staff_portal_user and request.user.can('bookings.view'):
        if request.user.role and request.user.role.code == 'reception' \
                and request.user.facility_id \
                and booking.facility_id != request.user.facility_id:
            raise PermissionDenied('Reception can only view bookings for the assigned facility.')
        return booking, True
    raise PermissionDenied('You can only view your own applications.')


def _cancel_open_workflow(booking, actor, note):
    instance = booking.workflow_instance
    if instance and instance.status in ('running', 'returned'):
        instance.status = 'cancelled'
        instance.note = note[:255]
        instance.completed_at = timezone.now()
        instance.current_step = None
        instance.save(update_fields=['status', 'note', 'completed_at', 'current_step'])
        instance.tasks.filter(status='pending').update(status='cancelled')


@transaction.atomic
def cancel_booking(booking, actor, reason, refund_request=True):
    """Cancel an open or paid booking; paid bookings open a refund request.

    The booking row is locked so a concurrent cancel, payment callback or
    workflow decision cannot double-cancel or double-refund.
    """
    booking = Booking.objects.select_for_update().get(pk=booking.pk)
    if booking.status in ('cancelled', 'rejected', 'expired', 'completed'):
        return False, 'This booking cannot be cancelled in its current status.'
    from_status = booking.status
    refund_created = None
    if booking.payment is not None and refund_request:
        percent, _ = availability.refund_percent(max(0, booking.days_until_checkin))
        amount = (booking.total * percent / Decimal('100')).quantize(Decimal('0.01'))
        refund_created = Refund.objects.create(
            booking=booking, payment=booking.payment, amount=amount, percent=percent,
            reason=reason, requested_by=actor,
        )
        booking.refund_status = 'requested'
        booking.refund_percent = percent
        booking.refund_amount = amount
        booking.refund_requested_at = timezone.now()
    booking.status = 'cancelled'
    booking.cancelled_at = timezone.now()
    booking.cancelled_by = actor
    booking.cancellation_reason = reason[:255]
    booking.hold_expires_at = None
    booking.save()
    release_booking_locks(booking)
    BookingStatusChange.objects.create(
        booking=booking, from_status=from_status, to_status='cancelled',
        actor=actor, comment=reason[:255],
    )
    _cancel_open_workflow(booking, actor, reason)
    send(booking.applicant, 'status_update', {
        'reference': booking.reference,
        'subject': f'Booking {booking.reference} cancelled',
        'message': reason,
    }, url=f'/bookings/{booking.pk}/', channels=['inapp', 'email', 'sms'])
    log(actor, 'update', booking, f'Cancelled: {reason}', module='bookings')
    return True, refund_created


def _verify_url(request, booking):
    return request.build_absolute_uri(
        reverse('verify_permit', args=[booking.permit_token]))


# ------------------------------------------------------------------- public
def facility_public(request, code):
    facility = get_object_or_404(
        Facility.objects.prefetch_related('units', 'units__tariffs'), code=code,
        is_active=True)
    start = parse_date(request.GET.get('from')) or today()
    calendar = availability.facility_calendar(facility, start, 35,
                                              asset_category='dakbungalow')
    units = facility.units.filter(is_active=True, asset_category='dakbungalow'
                                  ).prefetch_related('tariffs')
    return render(request, 'bookings/facility_public.html', {
        'facility': facility,
        'units': units,
        'calendar': calendar,
        'start': start,
        'categories': [c[0] for c in Booking.CATEGORIES],
        'page_title': facility.name,
        'required_docs': REQUIRED_DOCS,
    })


# ------------------------------------------------------------------- citizen
@citizen_required
def citizen_home(request):
    rows = Booking.objects.filter(applicant=request.user).select_related(
        'facility', 'unit').order_by('-created_at')
    active = rows.filter(status__in=['submitted', 'under_review', 'clarification',
                                     'recommended', 'approved', 'awaiting_payment', 'paid'])
    page = paginate(request, rows, 10)
    for booking in page:
        booking.journey_info = build_journey(booking, request.user)
    return render(request, 'bookings/citizen_home.html', {
        'bookings': page,
        'page_obj': page,
        'active_count': active.count(),
        'page_title': 'My applications',
        'draft': request.session.get('booking_draft'),
    })


@citizen_required
def apply_start(request, code):
    facility = get_object_or_404(Facility, code=code, is_active=True)
    if request.method == 'POST':
        form = ApplyForm(request.POST, asset_category='dakbungalow')
        if form.is_valid():
            data = form.cleaned_data
            unit = data['unit']
            check_in = data['check_in']
            check_out = data['check_out']
            slot = data['slot'] if unit.is_hall else ''
            price = quote(unit, data['category'], check_in, check_out, slot)
            request.session['booking_draft'] = {
                'facility_id': facility.pk,
                'unit_id': unit.pk,
                'category': data['category'],
                'check_in': check_in.isoformat(),
                'check_out': check_out.isoformat(),
                'slot': slot,
                'guests': data['guests'],
            }
            return redirect('apply_details')
    else:
        form = ApplyForm(initial={'facility': facility, 'check_in': today() + timedelta(days=1),
                                  'check_out': today() + timedelta(days=2), 'guests': 1})
    units = facility.units.filter(is_active=True, asset_category='dakbungalow'
                                  ).prefetch_related('tariffs')
    return render(request, 'bookings/apply_start.html', {
        'facility': facility, 'form': form, 'units': units,
        'calendar': availability.facility_calendar(facility, today(), 35,
                                                   asset_category='dakbungalow'),
        'calendar_leading': list(range(today().weekday())),
        'slot_choices': availability.SLOT_CHOICES,
        'page_title': f'Apply - {facility.name}',
    })


@citizen_required
@transaction.atomic
def apply_details(request):
    draft = request.session.get('booking_draft')
    if not draft:
        messages.info(request, 'Choose a facility and dates first.')
        return redirect('home')
    unit = get_object_or_404(Unit.objects.select_related('facility'), pk=draft['unit_id'])
    check_in = parse_date(draft['check_in'])
    check_out = parse_date(draft['check_out'])
    slot = draft.get('slot', '')
    price = quote(unit, draft['category'], check_in, check_out, slot)
    if price is None:
        messages.error(request, 'No tariff is published for this category.')
        return redirect('home')

    if request.method == 'POST':
        form = DetailsForm(request.POST, category=draft['category'])
        if form.is_valid() and form.cleaned_data['guests'] > unit.capacity:
            form.add_error('guests', 'The number of guests exceeds the selected asset capacity.')
        if form.is_valid():
            if not is_free(unit, check_in, check_out, slot):
                messages.error(request, 'The inventory was taken while you were applying. '
                                        'Please choose another room or date.')
                return redirect('apply_start', code=unit.facility.code)
            hold_until = timezone.now() + timedelta(hours=availability.hold_hours())
            booking = Booking.objects.create(
                applicant=request.user,
                facility=unit.facility,
                unit=unit,
                category=draft['category'],
                check_in=check_in,
                check_out=check_out,
                slot=slot,
                guests=form.cleaned_data['guests'],
                purpose=form.cleaned_data['purpose'],
                contact_phone=form.cleaned_data.get('contact_phone') or request.user.phone,
                national_id=form.cleaned_data.get('national_id', ''),
                office_id=form.cleaned_data.get('office_id', ''),
                notes=form.cleaned_data.get('notes', ''),
                payment_flow=draft.get('payment_flow', 'approval_first'),
                amount=price['charges'],
                deposit=price['deposit'],
                gateway_charge=price['gateway_charge'],
                total=price['total'],
                price_breakdown=price['lines'],
                hold_expires_at=hold_until,
            )
            try:
                with transaction.atomic():
                    availability.release_expired_holds([unit])
                    take_hold(unit, daterange_days(check_in, check_out), slot, hold_until,
                              booking=booking)
            except IntegrityError:
                booking.delete()
                messages.error(request, 'Another application just took that inventory. '
                                        'Please pick different dates.')
                return redirect('apply_start', code=unit.facility.code)

            for upload in request.FILES.getlist('documents')[:5]:
                try:
                    validate_upload(upload, 'Supporting document')
                except ValidationError as exc:
                    messages.warning(request, '; '.join(exc.messages))
                    continue
                BookingDocument.objects.create(
                    booking=booking, label=upload.name[:120], file=upload,
                    kind='supporting', uploaded_by=request.user)

            template = WorkflowTemplate.objects.filter(code='booking', is_active=True).first()
            if template is None:
                release_booking_locks(booking)
                booking.delete()
                messages.error(request, 'The booking workflow is not configured. '
                                        'Ask the administrator to check the workflow designer.')
                return redirect('home')
            payload = {
                'subject': f'{booking.applicant_name} - {unit.facility.name} / {unit.name}',
                'url': reverse('booking_detail', args=[booking.pk]),
                'amount': float(booking.total),
                'nights': booking.nights,
                'unit_kind': unit.kind,
                'facility': unit.facility.code,
                'applicant_category': booking.category,
                'slot': booking.slot or 'room',
                'check_in': booking.check_in.isoformat(),
                'check_out': booking.check_out.isoformat(),
            }
            engine.start(template, booking, payload, request.user,
                         tracking_id=booking.reference)
            send(request.user, 'confirmation', {
                'reference': booking.reference,
                'subject': f'Application received - {booking.reference}',
                'message': f'Your application for {booking.facility.name} / '
                           f'{booking.unit.name} was received and is under review.',
            }, url=f'/bookings/{booking.pk}/', channels=['inapp', 'email', 'sms'])
            request.session.pop('booking_draft', None)
            if booking.payment_flow == 'direct':
                booking.refresh_from_db()
                payment = start_payment(booking)
                return redirect('gateway_checkout', txn_id=payment.txn_id)
            return redirect('booking_submitted', pk=booking.pk)

    else:
        last = Booking.objects.filter(applicant=request.user).exclude(
            national_id='').order_by('-created_at').first()
        form = DetailsForm(
            initial={'guests': draft.get('guests', 1),
                     'contact_phone': request.user.phone,
                     'national_id': last.national_id if last else '',
                     'office_id': last.office_id if last else ''},
            category=draft['category'])
    return render(request, 'bookings/apply_details.html', {
        'unit': unit, 'facility': unit.facility, 'price': price, 'draft': draft,
        'category_label': dict(Booking.CATEGORIES).get(draft['category'], draft['category']),
        'form': form, 'check_in': check_in, 'check_out': check_out, 'slot': slot,
        'required_docs': REQUIRED_DOCS.get(draft['category'], ''),
        'page_title': 'Review and submit',
    })


@citizen_required
def booking_submitted(request, pk):
    booking = get_object_or_404(Booking, pk=pk, applicant=request.user)
    return render(request, 'bookings/submitted.html', {
        'booking': booking,
        'journey': build_journey(booking, request.user),
        'page_title': 'Application submitted',
    })


def _thread_context(request, booking):
    documents = booking.documents.select_related('uploaded_by')
    return {
        'booking': booking,
        'workflow': booking.workflow_instance,
        'records': booking.workflow_instance.records.select_related(
            'actor', 'step') if booking.workflow_instance else [],
        'payment': booking.payment,
        'payments': booking.payments.order_by('-initiated_at'),
        'refunds': booking.refunds.order_by('-created_at'),
        'documents': documents,
        'messages_list': booking.messages.select_related('author'),
        'history': booking.status_changes.select_related('actor'),
        'verify_url': _verify_url(request, booking),
        'refund_policy': availability.refund_policy_text(),
        'journey': build_journey(booking, request.user),
    }


@login_required
def booking_detail(request, pk):
    booking, is_staff = _get_booking(request, pk)
    return render(request, 'bookings/detail.html', {
        **_thread_context(request, booking),
        'is_staff_view': is_staff,
        'page_title': booking.reference,
        'today': today(),
    })


@require_POST
@login_required
def booking_message(request, pk):
    booking, is_staff = _get_booking(request, pk)
    if request.user.is_read_only:
        raise PermissionDenied('Read-only roles cannot post messages.')
    body = (request.POST.get('body') or '').strip()
    if not body:
        messages.error(request, 'Write a message before sending.')
        return redirect('booking_detail', pk=booking.pk)
    BookingMessage.objects.create(
        booking=booking, author=request.user, body=body,
        is_internal=request.POST.get('internal') == '1' and is_staff)
    if is_staff:
        send(booking.applicant, 'status_update', {
            'reference': booking.reference,
            'subject': f'Message about {booking.reference}',
            'message': body,
        }, url=f'/bookings/{booking.pk}/', channels=['inapp', 'email'])
    else:
        instance = booking.workflow_instance
        if instance and instance.status == 'returned':
            engine.resume(instance, request.user, body[:200])
            messages.success(request, 'Your response was sent and the application is back under review.')
        else:
            messages.success(request, 'Message added. The booking desk can see it.')
    log(request.user, 'update', booking, 'Booking message added', module='bookings')
    return redirect('booking_detail', pk=booking.pk)


@require_POST
@login_required
def booking_upload(request, pk):
    booking, _ = _get_booking(request, pk)
    upload = request.FILES.get('file')
    if not upload:
        messages.error(request, 'Choose a file to upload.')
        return redirect('booking_detail', pk=booking.pk)
    try:
        validate_upload(upload, 'Document')
    except ValidationError as exc:
        messages.error(request, '; '.join(exc.messages))
        return redirect('booking_detail', pk=booking.pk)
    BookingDocument.objects.create(
        booking=booking, label=(request.POST.get('label') or upload.name)[:120],
        file=upload, kind='evidence', uploaded_by=request.user)
    log(request.user, 'upload', booking, f'Uploaded {upload.name}', module='bookings')
    messages.success(request, 'Document attached.')
    return redirect('booking_detail', pk=booking.pk)


@require_POST
@login_required
def booking_cancel(request, pk):
    booking, is_staff = _get_booking(request, pk)
    if request.user.is_read_only:
        raise PermissionDenied('Read-only roles cannot cancel bookings.')
    reason = (request.POST.get('reason') or 'Cancelled by the applicant').strip()
    ok, result = cancel_booking(booking, request.user, reason)
    if not ok:
        messages.error(request, result)
    elif result is not None:
        messages.success(request, f'Booking cancelled. Refund request {money(result.amount)} '
                                  f'({result.percent}%) is awaiting finance processing.')
    else:
        messages.success(request, 'Booking cancelled and the held inventory released.')
    return redirect('booking_detail', pk=booking.pk)


@require_POST
@login_required
def start_booking_payment(request, pk):
    booking, _ = _get_booking(request, pk)
    if booking.applicant_id != request.user.pk and not request.user.can('bookings.finance'):
        raise PermissionDenied('Only the applicant can pay for this booking.')
    if not booking.can_pay:
        messages.error(request, 'This booking is not awaiting payment, or the payment window closed.')
        return redirect('booking_detail', pk=booking.pk)
    payment = start_payment(booking)
    return redirect('gateway_checkout', txn_id=payment.txn_id)


@login_required
def booking_receipt(request, pk):
    booking, _ = _get_booking(request, pk)
    payment = booking.payment
    if payment is None:
        messages.error(request, 'No verified payment exists for this booking.')
        return redirect('booking_detail', pk=booking.pk)
    return receipt_pdf(booking, payment)


@login_required
def booking_permit(request, pk):
    booking, _ = _get_booking(request, pk)
    if not booking.permit_issued_at:
        messages.error(request, 'A permit is issued only after the required approvals '
                                'and a verified payment.')
        return redirect('booking_detail', pk=booking.pk)
    return permit_pdf(booking, _verify_url(request, booking))


@login_required
def booking_qr(request, pk):
    from core.pdf import qr_png_bytes

    booking, _ = _get_booking(request, pk)
    return HttpResponse(qr_png_bytes(_verify_url(request, booking)),
                        content_type='image/png')


@login_required
def booking_quote_pdf(request, pk):
    booking, _ = _get_booking(request, pk)
    from core.pdf import simple_pdf

    meta = [
        ('Reference', booking.reference),
        ('Applicant', booking.applicant_name),
        ('Facility', f'{booking.facility.name} - {booking.unit.name}'),
        ('Dates', f'{booking.check_in} to {booking.check_out}'),
        ('Category', booking.get_category_display()),
        ('Charges', money(booking.amount)),
        ('Security deposit', money(booking.deposit)),
        ('Gateway charge', money(booking.gateway_charge)),
        ('Total', money(booking.total)),
        ('Status', booking.status_label),
    ]
    return simple_pdf(f'{booking.reference}-application.pdf', 'Booking application',
                      'Application summary (not a permit)', meta=meta,
                      sections=[('Price breakdown', '\n'.join(
                          f'{line["label"]}: {money(line["amount"])}'
                          for line in booking.price_breakdown) or 'Sample tariff')])


# --------------------------------------------------------------------- staff
@perm_required('bookings.view')
def staff_list(request):
    rows = _staff_booking_queryset(request.user)
    status = request.GET.get('status', '')
    facility = request.GET.get('facility', '')
    queue = request.GET.get('queue', '')
    q = request.GET.get('q', '').strip()
    date_from = parse_date(request.GET.get('from'))
    date_to = parse_date(request.GET.get('to'))

    if status:
        rows = rows.filter(status=status)
    if facility:
        rows = rows.filter(facility__code=facility)
    if date_from:
        rows = rows.filter(check_in__gte=date_from)
    if date_to:
        rows = rows.filter(check_in__lte=date_to)
    if q:
        rows = rows.filter(
            Q(reference__icontains=q) | Q(purpose__icontains=q)
            | Q(applicant__first_name__icontains=q)
            | Q(applicant__last_name__icontains=q)
            | Q(applicant__username__icontains=q))
    if queue == 'desk':
        rows = rows.filter(status__in=['submitted', 'under_review', 'clarification'])
    elif queue == 'reviews':
        rows = rows.filter(status__in=['recommended', 'approved', 'awaiting_payment'])
    elif queue == 'reception':
        rows = rows.filter(status__in=['paid', 'completed'], check_in__lte=today() + timedelta(days=2))

    rows = rows.order_by('-created_at')
    counts = {code: 0 for code, _ in STATUSES}
    for row in _staff_booking_queryset(request.user).values('status').annotate(n=Count('id')):
        counts[row['status']] = row['n']
    day = today()
    assets = asset_status(day)
    free_today = next(row['free'] for row in assets if row['code'] == 'dakbungalow')
    return render(request, 'bookings/staff_list.html', {
        'page_obj': paginate(request, rows, 20),
        'counts': counts,
        'statuses': STATUSES,
        'facilities': Facility.objects.filter(is_active=True),
        'available_units': free_today,
        'assets': assets,
        'status': status, 'facility': facility, 'queue': queue, 'q': q,
        'page_title': 'Booking management',
    })


@perm_required('bookings.view')
def staff_detail(request, pk):
    booking, _ = _get_booking(request, pk)
    return render(request, 'bookings/detail.html', {
        **_thread_context(request, booking),
        'is_staff_view': True,
        'statuses': STATUSES,
        'page_title': booking.reference,
        'today': today(),
    })


@perm_required('bookings.reception')
def reception_desk(request):
    facility = request.user.facility
    rows = Booking.objects.select_related('facility', 'unit', 'applicant').filter(
        status__in=['paid', 'completed'])
    if facility:
        rows = rows.filter(facility=facility)
    found = None
    reference = ''
    if request.GET.get('reference'):
        reference = request.GET['reference'].strip()
        found = rows.filter(reference__iexact=reference).first()
        if found is None:
            messages.warning(request, f'No confirmed booking found for "{reference}" at your facility.')
    upcoming = rows.filter(check_in__lte=today() + timedelta(days=3)).order_by('check_in')[:30]
    return render(request, 'bookings/reception.html', {
        'bookings': upcoming, 'found': found, 'reference': reference,
        'facility': facility, 'page_title': 'Reception desk', 'today': today(),
    })


@require_POST
@perm_required('bookings.reception')
def reception_checkin(request, pk):
    booking, _ = _get_booking(request, pk)
    if request.user.facility_id and booking.facility_id != request.user.facility_id:
        raise PermissionDenied('This booking is for a different facility.')
    if booking.status not in ('paid', 'completed'):
        messages.error(request, 'Only paid and confirmed bookings can be checked in.')
    elif booking.check_in > today() + timedelta(days=1):
        messages.error(request, 'Check-in opens one day before the booking date.')
    else:
        booking.checked_in_at = timezone.now()
        booking.checked_in_by = request.user
        booking.save(update_fields=['checked_in_at', 'checked_in_by'])
        messages.success(request, f'Checked in {booking.applicant_name} for {booking.reference}.')
        log(request.user, 'verify', booking, 'Reception check-in', module='bookings')
    return redirect('reception_desk')


@require_POST
@perm_required('bookings.reception')
def reception_checkout(request, pk):
    booking, _ = _get_booking(request, pk)
    if request.user.facility_id and booking.facility_id != request.user.facility_id:
        raise PermissionDenied('This booking is for a different facility.')
    if booking.status != 'paid':
        messages.error(request, 'Only a paid, checked-in booking can be checked out.')
    else:
        booking.checked_out_at = timezone.now()
        if not booking.checked_in_at:
            booking.checked_in_at = timezone.now()
        from_status = booking.status
        booking.status = 'completed'
        booking.save(update_fields=['checked_out_at', 'checked_in_at', 'status', 'updated_at'])
        BookingStatusChange.objects.create(
            booking=booking, from_status=from_status, to_status='completed',
            actor=request.user, comment='Checked out at reception')
        messages.success(request, f'{booking.reference} marked completed.')
        log(request.user, 'verify', booking, 'Reception check-out', module='bookings')
    return redirect('reception_desk')


@require_POST
@perm_required('bookings.cancel')
def staff_cancel(request, pk):
    booking, _ = _get_booking(request, pk)
    reason = (request.POST.get('reason') or 'Cancelled by the Parishad').strip()
    ok, result = cancel_booking(booking, request.user, reason)
    if not ok:
        messages.error(request, result)
    elif result is not None:
        messages.success(request, f'Cancelled. Refund request {money(result.amount)} created.')
    else:
        messages.success(request, 'Booking cancelled and inventory released.')
    return redirect('staff_detail', pk=booking.pk)


@perm_required('bookings.view')
def staff_export(request):
    rows = _staff_booking_queryset(request.user)
    data = [['Reference', 'Applicant', 'Category', 'Facility', 'Unit', 'Check-in',
             'Check-out', 'Slot', 'Status', 'Total', 'Payment', 'Created']]
    for b in rows[:2000]:
        data.append([b.reference, b.applicant_name, b.get_category_display(),
                     b.facility.name, b.unit.name, b.check_in, b.check_out,
                     b.slot or 'room', b.status_label, b.total,
                     b.payment_txn_id, b.created_at.strftime('%Y-%m-%d %H:%M')])
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="bookings.csv"'
    writer = csv.writer(response)
    writer.writerows(data)
    log(request.user, 'export', None, 'Booking list exported', module='bookings')
    return response
