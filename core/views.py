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
from accounts.models import Role, User
from audit.models import AuditEntry, log
from bookings.journey import booking_route
from bookings.models import Booking
from core.assets import asset_status
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
from hr.models import Attendance, Employee
from meetings.models import ActionItem, Meeting
from notifications.models import Notification
from payments.models import Payment, Refund
from workflow.models import WorkflowTask


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
    if code == 'bng':
        code = 'bn'
    if code not in ('en', 'bn'):
        code = 'en'
    request.session['gzp_lang'] = code
    target = request.GET.get('next') or '/'
    if not url_has_allowed_host_and_scheme(
            target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        target = '/'
    return HttpResponseRedirect(target)


def _mail_summary(user, day):
    qs = Notification.objects.filter(user=user, channel='inapp')
    items = list(qs.order_by('-created_at')[:3])
    for item in items:
        item.preview = ' '.join((item.body or '').split())[:110]
    return {
        'unread': qs.filter(read_at__isnull=True).count(),
        'today': qs.filter(created_at__date=day).count(),
        'items': items,
    }


def _attendance_summary(day):
    rows = list(Attendance.objects.filter(date=day).select_related('employee'))
    active = Employee.objects.filter(status='active')
    active_total = active.count()
    marked_active = len([row for row in rows if row.employee.status == 'active'])
    present = [row.employee.name for row in rows if row.status in ('present', 'late')]
    absent = [row.employee.name for row in rows if row.status == 'absent']
    on_leave = [row.employee.name for row in rows if row.status == 'leave']
    missing = active.exclude(pk__in=[row.employee_id for row in rows])
    missing_names = list(missing.values_list('name', flat=True)[:3])
    return {
        'recorded': bool(rows),
        'total': active_total,
        'present': len(present),
        'present_names': present[:3],
        'present_more': max(0, len(present) - 3),
        'absent': len(absent),
        'absent_names': absent[:3],
        'absent_more': max(0, len(absent) - 3),
        'leave': len(on_leave),
        'leave_names': on_leave[:3],
        'leave_more': max(0, len(on_leave) - 3),
        'not_marked': active_total - marked_active,
        'not_marked_names': missing_names,
        'not_marked_more': max(0, active_total - marked_active - len(missing_names)),
    }


def _meeting_summary(day):
    todays_qs = Meeting.objects.filter(date=day).exclude(status='cancelled')
    today_count = todays_qs.count()
    todays = list(todays_qs.select_related('chair').order_by('start_time', 'pk')[:3])
    upcoming = list(
        Meeting.objects.filter(date__gt=day, status='scheduled')
        .select_related('chair').order_by('date', 'start_time', 'pk')[:3])
    return {
        'today': todays,
        'count': today_count,
        'upcoming': upcoming,
        'next': todays[0] if todays else (upcoming[0] if upcoming else None),
        'open_actions': ActionItem.objects.exclude(
            status__in=('done', 'cancelled')).count(),
    }


def _revenue_summary(day):
    month_start = day.replace(day=1)
    verified = Payment.objects.filter(status='success', verified_at__isnull=False)
    pending = Booking.objects.filter(status='awaiting_payment')
    return {
        'month': verified.filter(verified_at__date__gte=month_start)
                  .aggregate(total=Sum('amount'))['total'] or 0,
        'today': verified.filter(verified_at__date=day)
                 .aggregate(total=Sum('amount'))['total'] or 0,
        'payments': verified.filter(verified_at__date__gte=month_start).count(),
        'pending': pending.aggregate(total=Sum('total'))['total'] or 0,
        'pending_count': pending.count(),
    }


def _approval_summary(user):
    pending = WorkflowTask.objects.filter(status='pending').select_related(
        'instance', 'step', 'role', 'assignee')
    mine = pending.filter(Q(role=user.role) | Q(assignee=user))
    return {
        'pending': pending.count(),
        'mine': mine.count(),
        'desk': pending.filter(role=user.role).count() if user.role else 0,
        'overdue': pending.filter(due_at__lt=timezone.now()).count(),
        'waiting': list(mine.order_by('due_at')[:3]),
    }


def _application_summary(day):
    confirmed = Booking.objects.filter(status__in=('paid', 'completed'))
    return {
        'arrivals': list(confirmed.filter(check_in=day).select_related(
            'facility', 'unit')[:3]),
        'departures': list(confirmed.filter(check_out=day).select_related(
            'facility', 'unit')[:3]),
        'arrival_count': confirmed.filter(check_in=day).count(),
        'departure_count': confirmed.filter(check_out=day).count(),
        'in_house': confirmed.filter(check_in__lt=day, check_out__gt=day).count(),
        'new_today': Booking.objects.filter(created_at__date=day).count(),
        'recent': Booking.objects.select_related('facility', 'unit', 'applicant')[:3],
    }


def _admin_summary():
    return {
        'users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'roles': Role.objects.count(),
        'backup': BackupRecord.objects.order_by('-created_at').first(),
        'health': list(HealthEvent.objects.order_by('-created_at')[:3]),
        'audit': list(AuditEntry.objects.select_related('actor').order_by(
            '-created_at')[:3]),
        'settings_changed': AppSetting.objects.order_by('-updated_at')[:3],
    }


def _dashboard_alerts(user):
    alerts = []
    stale = Booking.objects.filter(
        status='awaiting_payment', payment_deadline__lt=timezone.now()).count()
    if stale:
        alerts.append({
            'level': 'warning',
            'count': stale,
            'text_key': 'approved booking(s) passed the payment window.',
            'url': '/app/bookings/?status=awaiting_payment',
        })
    refunds = Booking.objects.filter(refund_status='requested').count()
    if refunds and user.can('payments.refund'):
        alerts.append({
            'level': 'info',
            'count': refunds,
            'text_key': 'refund request(s) awaiting finance action.',
            'url': '/app/refunds/',
        })
    overdue = WorkflowTask.objects.filter(
        status='pending', due_at__lt=timezone.now()).count()
    if overdue:
        alerts.append({
            'level': 'danger',
            'count': overdue,
            'text_key': 'approval task(s) are overdue.',
            'url': '/app/tasks/?status=overdue',
        })
    return alerts


def _role_focus(user, day, approvals, meetings):
    facility = user.facility
    if user.can('bookings.reception'):
        rows = Booking.objects.filter(
            status__in=('paid', 'completed'), check_in=day)
        if facility:
            rows = rows.filter(facility=facility)
        return {
            'label': 'Arrivals today', 'value': rows.count(),
            'hint': 'Guests to check in at the desk', 'url': '/app/reception/',
            'icon': 'box-arrow-in-right',
        }
    if user.can('payments.refund'):
        count = Refund.objects.filter(status='requested').count()
        return {
            'label': 'Refunds to process', 'value': count,
            'hint': 'Requests waiting for finance', 'url': '/app/refunds/',
            'icon': 'arrow-counterclockwise',
        }
    if user.can('hr.attendance'):
        rows = Attendance.objects.filter(date=day)
        present = rows.filter(status__in=('present', 'late')).count()
        return {
            'label': 'Staff present today',
            'value': f'{present}/{Employee.objects.filter(status="active").count()}',
            'hint': 'Marked on the attendance register',
            'url': '/app/hr/attendance/', 'icon': 'calendar2-check',
        }
    if user.can('meetings.manage'):
        return {
            'label': 'Meetings today', 'value': meetings['count'],
            'hint': 'Scheduled for today', 'url': '/app/meetings/',
            'icon': 'calendar-event',
        }
    return {
        'label': 'Approvals waiting', 'value': approvals['desk'],
        'hint': 'Waiting at your desk', 'url': '/app/tasks/?status=open',
        'icon': 'inbox',
    }


@staff_required
def dashboard(request):
    user = request.user
    org = getattr(user, 'organization', None)
    if org is not None and org.is_city and user.can('city.view'):
        return redirect('/app/city/')
    day = today()
    mail = _mail_summary(user, day)
    attendance = _attendance_summary(day)
    meetings = _meeting_summary(day)
    revenue = _revenue_summary(day)
    approvals = _approval_summary(user)
    applications = _application_summary(day)
    route = booking_route(user)
    my_step = next((step for step in route if step['is_mine']), None)
    my_tasks = WorkflowTask.objects.select_related(
        'instance', 'step').filter(
            Q(role=user.role) | Q(assignee=user), status='pending'
        ).order_by('due_at')[:3]

    context = {
        'today': day,
        'alerts': _dashboard_alerts(user),
        'mail': mail,
        'attendance': attendance,
        'meetings': meetings,
        'revenue': revenue,
        'approvals': approvals,
        'applications': applications,
        'route': route,
        'my_step': my_step,
        'my_tasks_list': my_tasks,
        'asset_status': asset_status(day),
        'my_pending': approvals['mine'],
        'overdue_tasks': approvals['overdue'],
        'pending_tasks': approvals['pending'],
    }
    if user.can('bookings.approve_ceo'):
        context['page_title'] = 'CEO dashboard'
        return render(request, 'core/dashboard_ceo.html', context)
    if user.can('accounts.manage_settings'):
        context.update({'admin_info': _admin_summary(), 'page_title': 'Administrator dashboard'})
        return render(request, 'core/dashboard_admin.html', context)
    context.update({
        'focus': _role_focus(user, day, approvals, meetings),
        'page_title': 'My dashboard',
    })
    return render(request, 'core/dashboard_role.html', context)


@perm_required('accounts.manage_settings')
def settings_page(request):
    defs = {d[0]: d for d in SETTING_DEFS}
    if request.method == 'POST' and request.POST.get('form') == 'org':
        from organizations.models import Organization
        org = (Organization.objects.filter(
            code=request.session.get('gzp_org', '')).first()
            or getattr(request.user, 'organization', None)
            or Organization.objects.filter(code='gzp').first())
        if org:
            org.head_title = (request.POST.get('head_title') or '').strip() or org.head_title
            org.head_name = (request.POST.get('head_name') or '').strip()
            org.save(update_fields=['head_title', 'head_name'])
            log(request.user, 'settings', org,
                f'{org.name}: head label set to {org.head_title}', module='organizations')
            messages.success(request, f'{org.name}: organisation details saved.')
        return redirect('settings')
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
        'history': paginate(request, AppSetting.objects.exclude(
            updated_at__isnull=True).order_by('-updated_at', 'pk'), 20),
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
        'backups': paginate(request, BackupRecord.objects.select_related('created_by'), 20),
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
    events = paginate(request, HealthEvent.objects.all(), 30)
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
