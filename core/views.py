from __future__ import annotations

import sqlite3
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.db import connection
from django.db.models import Count, Q, Sum
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.decorators import perm_required, staff_required
from audit.models import AuditEntry, log
from bookings.models import STATUSES, Booking
from core.defaults import SETTING_DEFS
from core.models import (
    AppSetting,
    BackupRecord,
    HealthEvent,
    get_int,
    get_setting,
    set_setting,
)
from core.utils import money, paginate, parse_date, today
from facilities.availability import available_units
from facilities.models import Facility
from workflow.models import WorkflowInstance, WorkflowTask


def home(request):
    facilities = list(Facility.objects.filter(is_active=True).prefetch_related(
        'units', 'units__tariffs'))
    check_in = parse_date(request.GET.get('check_in')) or (today() + timedelta(days=1))
    check_out = parse_date(request.GET.get('check_out')) or (check_in + timedelta(days=1))
    if check_out <= check_in:
        check_out = check_in + timedelta(days=1)
    facility_code = request.GET.get('facility', '')
    show = [f for f in facilities if not facility_code or f.code == facility_code]
    for facility in facilities:
        if facility in show:
            try:
                facility.available_count = len(available_units(facility, check_in, check_out))
            except Exception:
                facility.available_count = 0
    return render(request, 'core/home.html', {
        'facilities': facilities,
        'visible_facilities': show,
        'check_in': check_in,
        'check_out': check_out,
        'facility_code': facility_code,
        'page_title': 'Dakbungalow booking',
        'public_page': True,
    })


def track(request):
    reference = (request.GET.get('reference') or request.POST.get('reference') or '').strip()
    booking = None
    searched = bool(reference)
    if reference:
        booking = Booking.objects.select_related('facility', 'unit').filter(
            reference__iexact=reference).first()
    return render(request, 'core/track.html', {
        'reference': reference,
        'booking': booking,
        'searched': searched,
        'page_title': 'Track application',
    })


def verify_permit(request, token):
    booking = Booking.objects.select_related('facility', 'unit', 'applicant').filter(
        permit_token=token).first()
    valid = bool(booking and booking.status in ('paid', 'completed'))
    return render(request, 'core/verify.html', {
        'booking': booking,
        'valid': valid,
        'page_title': 'Permit verification',
        'now': timezone.now(),
    })


def set_language(request, code):
    if code not in ('en', 'bn'):
        code = 'en'
    request.session['gzp_lang'] = code
    target = request.GET.get('next') or '/'
    if not url_has_allowed_host_and_scheme(
            target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        target = '/'
    return HttpResponseRedirect(target)


@staff_required
def dashboard(request):
    status_counts = {code: 0 for code, _ in STATUSES}
    for row in Booking.objects.values('status').annotate(n=Count('id')):
        status_counts[row['status']] = row['n']

    month_start = today().replace(day=1)
    collection = Booking.objects.filter(
        status__in=('paid', 'completed'), permit_issued_at__date__gte=month_start
    ).aggregate(total=Sum('total'))['total'] or 0

    next_week = today() + timedelta(days=7)
    upcoming = Booking.objects.filter(
        status__in=('paid', 'completed'), check_in__gte=today(), check_in__lt=next_week
    ).select_related('facility', 'unit', 'applicant').order_by('check_in')[:8]

    pending_all = WorkflowTask.objects.filter(status='pending')
    my_tasks = pending_all.filter(Q(role=request.user.role) | Q(assignee=request.user))
    overdue = pending_all.filter(due_at__lt=timezone.now())
    recent = Booking.objects.select_related('facility', 'unit', 'applicant')[:8]
    alerts = []
    stale = Booking.objects.filter(
        status='awaiting_payment', payment_deadline__lt=timezone.now()).count()
    if stale:
        alerts.append({
            'level': 'warning',
            'text': f'{stale} approved booking(s) passed the payment window and are awaiting release.',
            'url': '/app/bookings/?status=awaiting_payment',
        })
    unmatched = Booking.objects.filter(refund_status='requested').count()
    if unmatched and request.user.can('payments.refund'):
        alerts.append({
            'level': 'info',
            'text': f'{unmatched} refund request(s) awaiting finance action.',
            'url': '/app/refunds/',
        })
    if overdue:
        alerts.append({
            'level': 'danger',
            'text': f'{overdue.count()} workflow task(s) are overdue and need escalation review.',
            'url': '/app/tasks/?status=overdue',
        })

    by_facility = Facility.objects.filter(is_active=True).annotate(
        total=Count('bookings'),
        confirmed=Count('bookings', filter=Q(bookings__status__in=('paid', 'completed'))),
    )
    return render(request, 'core/dashboard.html', {
        'status_counts': status_counts,
        'status_rows': [(code, label, status_counts.get(code, 0))
                        for code, label in STATUSES],
        'total_bookings': Booking.objects.count(),
        'collection': collection,
        'upcoming': upcoming,
        'recent': recent,
        'pending_tasks': pending_all.count(),
        'my_pending': my_tasks.count(),
        'overdue_tasks': overdue.count(),
        'by_facility': by_facility,
        'alerts': alerts,
        'page_title': 'Dashboard',
        'today': today(),
    })


@perm_required('accounts.manage_settings')
def settings_page(request):
    defs = {d[0]: d for d in SETTING_DEFS}
    if request.method == 'POST':
        changed = []
        for key, (_, _default, _label, _group, _desc) in defs.items():
            if key not in request.POST:
                continue
            new = request.POST.get(key, '').strip()
            if key in ('app_name', 'demo_banner') and not new:
                continue
            if get_setting(key, _default) != new:
                set_setting(key, new, user=request.user, note='Updated in settings')
                changed.append(defs[key][2])
        log(request.user, 'settings', None,
            f'Settings updated: {", ".join(changed) or "no changes"}', module='core')
        messages.success(request, f'Settings saved. {len(changed)} value(s) changed.')
        return redirect('settings')

    groups = []
    for key, default, label, group, desc in SETTING_DEFS:
        row = next((g for g in groups if g['name'] == group), None)
        if row is None:
            row = {'name': group, 'items': []}
            groups.append(row)
        row['items'].append({
            'key': key, 'label': label, 'description': desc,
            'value': get_setting(key, default), 'default': default,
            'is_long': len(default) > 60,
            'is_bool': key in ('gateway_charge_paid_by_user', 'sms_client_paid'),
        })
    return render(request, 'core/settings.html', {
        'groups': groups,
        'history': AppSetting.objects.exclude(updated_at__isnull=True).order_by('-updated_at')[:20],
        'page_title': 'Settings and master data',
    })


def _run_backup(user):
    folder = Path(settings.BASE_DIR) / 'backups'
    folder.mkdir(exist_ok=True)
    stamp = timezone.localtime().strftime('%Y%m%d-%H%M%S')
    target = folder / f'gzp-backup-{stamp}.sqlite3'
    source = sqlite3.connect(str(settings.DATABASES['default']['NAME']))
    dest = sqlite3.connect(str(target))
    try:
        source.backup(dest)
    finally:
        dest.close()
        source.close()
    record = BackupRecord.objects.create(
        filename=target.name, size_bytes=target.stat().st_size,
        created_by=user, note='On-demand backup from the security page',
    )
    log(user, 'backup', record, f'Backup created: {target.name}', module='core')
    return record


def _verify_backup(record):
    path = Path(settings.BASE_DIR) / 'backups' / record.filename
    if not path.exists():
        return False, 'Backup file is missing.'
    try:
        conn = sqlite3.connect(str(path))
        result = conn.execute('PRAGMA integrity_check').fetchone()[0]
        tables = conn.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        conn.close()
    except sqlite3.Error as exc:
        return False, f'Backup could not be opened: {exc}'
    if result != 'ok':
        return False, f'Integrity check returned {result}.'
    return True, f'Integrity check ok. {tables} tables readable.'


@perm_required('accounts.manage_settings')
def security_page(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'backup':
            record = _run_backup(request.user)
            messages.success(request, f'Backup created: {record.filename} '
                                      f'({record.size_bytes / 1024:.0f} KB).')
        elif action == 'verify':
            record = get_object_or_404(BackupRecord, pk=request.POST.get('record'))
            ok, note = _verify_backup(record)
            if ok:
                record.verified = True
                record.verified_at = timezone.now()
                record.note = note
                record.save(update_fields=['verified', 'verified_at', 'note'])
                messages.success(request, f'Restore test passed. {note}')
            else:
                messages.error(request, f'Restore test failed. {note}')
            log(request.user, 'backup', record, f'Restore test: {note}', module='core')
        return redirect('security')

    controls = [
        {'title': 'Encryption', 'icon': 'shield-lock',
         'status': 'HTTPS/TLS in production; demo runs on localhost',
         'detail': 'Sensitive fields and backups are protected where the hosting architecture supports it. '
                   'In this offline demo the transport is local HTTP, shown honestly as simulated.',
         'kind': 'Simulated'},
        {'title': 'Firewall and WAF', 'icon': 'bricks',
         'status': 'Configuration committed, not enforceable on a laptop',
         'detail': 'Restrictive server firewall and web-layer rate limiting are part of the deployment '
                   'baseline. The app enforces upload validation, CSRF and role checks in code.',
         'kind': 'Configuration'},
        {'title': 'VPN / secure access', 'icon': 'globe2',
         'status': 'Documented; demo has no VPN',
         'detail': 'Management endpoints are separated by role and least privilege. VPN termination is a '
                   'hosting control and is shown as a deployment commitment.',
         'kind': 'Simulated'},
        {'title': 'Authentication', 'icon': 'person-badge',
         'status': 'Active',
         'detail': 'Password hashing, session timeout, login rate limiting, email/OTP verification, '
                   'role segregation and audit logs are implemented and testable.',
         'kind': 'Real'},
        {'title': 'Payment protection', 'icon': 'credit-card-2-front',
         'status': 'Active (simulated gateway)',
         'detail': 'Payments are confirmed only from HMAC-signed callbacks that the server verifies. '
                   'Duplicate and mismatched callbacks are stored and rejected.',
         'kind': 'Real logic'},
        {'title': 'Backup and recovery', 'icon': 'database-check',
         'status': 'Active',
         'detail': 'SQLite is copied with the online backup API into a timestamped folder. The restore '
                   'test opens the backup and runs an integrity check.',
         'kind': 'Real'},
        {'title': 'Monitoring and updates', 'icon': 'activity',
         'status': 'Active counters',
         'detail': 'Errors and availability counters are recorded. Patch and dependency management is a '
                   'maintenance commitment under the 36-month support plan.',
         'kind': 'Real counters'},
    ]
    return render(request, 'core/security.html', {
        'controls': controls,
        'backups': BackupRecord.objects.select_related('created_by')[:20],
        'page_title': 'Security and backup',
    })


@perm_required('accounts.manage_settings')
def health_page(request):
    db_ok, db_note = True, ''
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except Exception as exc:  # pragma: no cover - diagnostic only
        db_ok, db_note = False, str(exc)
    events = HealthEvent.objects.all()[:30]
    counts = {kind: HealthEvent.objects.filter(kind=kind).count()
              for kind, _ in HealthEvent.KIND}
    last_backup = BackupRecord.objects.order_by('-created_at').first()
    return render(request, 'core/health.html', {
        'db_ok': db_ok, 'db_note': db_note, 'events': events, 'counts': counts,
        'last_backup': last_backup,
        'backup_ok': bool(last_backup and last_backup.verified),
        'page_title': 'System health',
    })


@staff_required
def approvals_overview(request):
    return redirect('tasks')


def error_403(request, exception=None):
    return render(request, 'core/403.html', {'page_title': 'Access denied'}, status=403)


def error_404(request, exception=None):
    return render(request, 'core/404.html', {'page_title': 'Not found'}, status=404)


def error_500(request):
    return render(request, 'core/500.html', {'page_title': 'Server error'}, status=500)
