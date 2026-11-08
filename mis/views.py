from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q, Sum
from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import perm_required
from audit.models import AuditEntry, log
from bookings.models import STATUSES, Booking
from core.pdf import table_pdf
from core.utils import csv_response, get_client_ip, money, parse_date, today
from documents.models import DocumentFile
from facilities.models import Facility
from hr.models import Department, Employee
from meetings.models import ActionItem
from mis.models import ReportAccessLog
from payments.models import Payment, Refund
from projects.models import Project
from support.models import Ticket
from workflow.models import WorkflowInstance, WorkflowTask


def _serial(request, report, parameters=''):
    ReportAccessLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        report=report, parameters=parameters[:255], ip=get_client_ip(request),
    )
    log(request.user, 'view', None, f'Report viewed: {report} {parameters}'.strip(),
        request, module='mis')


def _month_series(months=6):
    anchor = today().replace(day=1)
    out = []
    for _ in range(months):
        out.append(anchor)
        anchor = (anchor - timedelta(days=1)).replace(day=1)
    return list(reversed(out))


@perm_required('mis.view_exec')
def executive(request):
    months = _month_series(6)
    series = []
    for start in months:
        end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        total = Booking.objects.filter(
            status__in=('paid', 'completed'), created_at__date__gte=start,
            created_at__date__lt=end,
        ).aggregate(v=Sum('total'))['v'] or 0
        series.append({'label': start.strftime('%b'), 'value': float(total)})

    collection = Booking.objects.filter(
        status__in=('paid', 'completed')).aggregate(v=Sum('total'))['v'] or 0
    refunded = Refund.objects.filter(status='processed').aggregate(v=Sum('amount'))['v'] or 0
    stats = {
        'bookings': Booking.objects.count(),
        'confirmed': Booking.objects.filter(status__in=('paid', 'completed')).count(),
        'collection': collection,
        'refunded': refunded,
        'net': collection - refunded,
        'employees': Employee.objects.filter(status='active').count(),
        'projects': Project.objects.exclude(status__in=('completed', 'cancelled')).count(),
        'tickets': Ticket.objects.exclude(status__in=('resolved', 'closed')).count(),
        'overdue_tasks': WorkflowTask.objects.filter(
            status='pending', due_at__lt=timezone.now()).count(),
    }
    status_counts = {code: 0 for code, _ in STATUSES}
    for row in Booking.objects.values('status').annotate(n=Count('id')):
        status_counts[row['status']] = row['n']
    facilities = Facility.objects.filter(is_active=True).annotate(
        total=Count('bookings'),
        confirmed=Count('bookings', filter=Q(bookings__status__in=('paid', 'completed'))),
        revenue=Sum('bookings__total', filter=Q(bookings__status__in=('paid', 'completed'))),
    )
    projects = Project.objects.exclude(status='cancelled').order_by('-budget')[:6]
    return render(request, 'mis/executive.html', {
        'stats': stats,
        'series': series,
        'status_counts': status_counts,
        'status_labels': dict(STATUSES),
        'facilities': facilities,
        'projects': projects,
        'page_title': 'Executive dashboard',
    })


@perm_required('mis.view_dept')
def department_dashboard(request):
    departments = []
    for dept in Department.objects.all():
        employees = Employee.objects.filter(department=dept)
        departments.append({
            'dept': dept,
            'employees': employees.count(),
            'on_leave': employees.filter(status='leave').count(),
            'projects': dept.projects.exclude(status__in=('completed', 'cancelled')).count(),
            'documents': dept.document_files.exclude(
                status__in=('closed', 'archived')).count(),
            'leaves': sum(1 for e in employees for _ in e.leaves.filter(status='submitted')),
        })
    actions = ActionItem.objects.exclude(status__in=('done', 'cancelled')).select_related(
        'meeting', 'owner')[:8]
    return render(request, 'mis/department.html', {
        'departments': departments,
        'actions': actions,
        'page_title': 'Department dashboard',
    })


def _booking_report_rows(request):
    qs = Booking.objects.select_related('facility', 'unit', 'applicant')
    date_from = parse_date(request.GET.get('from'))
    date_to = parse_date(request.GET.get('to'))
    facility = request.GET.get('facility', '')
    status = request.GET.get('status', '')
    if date_from:
        qs = qs.filter(check_in__gte=date_from)
    if date_to:
        qs = qs.filter(check_out__lte=date_to)
    if facility:
        qs = qs.filter(facility__code=facility)
    if status:
        qs = qs.filter(status=status)
    return qs.order_by('-created_at')


@perm_required('mis.reports')
def booking_report(request):
    qs = _booking_report_rows(request)
    totals = qs.aggregate(
        total=Sum('total'), amount=Sum('amount'), deposit=Sum('deposit'),
        gateway=Sum('gateway_charge'))
    status_counts = {code: 0 for code, _ in STATUSES}
    for row in qs.values('status').annotate(n=Count('id')):
        status_counts[row['status']] = row['n']
    by_facility = qs.values('facility__name').annotate(
        n=Count('id'), revenue=Sum('total')).order_by('-revenue')
    _serial(request, 'Booking and revenue report', request.GET.urlencode())
    return render(request, 'mis/bookings.html', {
        'page_obj': qs[:200],
        'totals': totals,
        'status_counts': status_counts,
        'by_facility': by_facility,
        'facilities': Facility.objects.all(),
        'statuses': STATUSES,
        'count': qs.count(),
        'page_title': 'Booking and revenue report',
    })


@perm_required('mis.reports', 'mis.export')
def report_export(request):
    report = request.GET.get('report', 'bookings')
    fmt = request.GET.get('format', 'csv')
    _serial(request, f'Export {report}', f'{fmt} {request.GET.urlencode()}')

    if report == 'revenue':
        headers = ['Month', 'Verified bookings', 'Collection']
        rows = []
        for start in _month_series(12):
            end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
            qs = Booking.objects.filter(
                status__in=('paid', 'completed'), created_at__date__gte=start,
                created_at__date__lt=end)
            rows.append([start.strftime('%Y-%m'),
                         qs.count(),
                         f'{qs.aggregate(v=Sum("total"))["v"] or 0:.2f}'])
    elif report == 'workflow':
        headers = ['Tracking', 'Template', 'Requester', 'Status', 'Created', 'Completed']
        rows = [[i.tracking_id, i.template.name,
                 i.requester.display_name if i.requester else '',
                 i.get_status_display(), i.created_at.strftime('%Y-%m-%d'),
                 i.completed_at.strftime('%Y-%m-%d') if i.completed_at else '']
                for i in WorkflowInstance.objects.select_related('template', 'requester')[:2000]]
    elif report == 'hr':
        headers = ['Employee', 'Department', 'Designation', 'Type', 'Status', 'Joined']
        rows = [[e.employee_no, e.name,
                 e.department.name if e.department else '',
                 e.designation.name if e.designation else '',
                 e.get_employment_type_display(), e.get_status_display(),
                 e.joining_date.isoformat() if e.joining_date else '']
                for e in Employee.objects.select_related('department', 'designation')]
    elif report == 'projects':
        headers = ['Code', 'Project', 'Status', 'Budget', 'Spent', 'Progress', 'End date']
        rows = [[p.code, p.name, p.get_status_display(), f'{p.budget:.2f}',
                 f'{p.spent:.2f}', f'{p.progress}%',
                 p.end_date.isoformat() if p.end_date else '']
                for p in Project.objects.all()]
    else:
        headers = ['Reference', 'Applicant', 'Facility', 'Unit', 'Check-in', 'Check-out',
                   'Status', 'Amount', 'Deposit', 'Gateway', 'Total']
        rows = [[b.reference, b.applicant_name, b.facility.name, b.unit.name,
                 b.check_in.isoformat(), b.check_out.isoformat(), b.status_label,
                 f'{b.amount:.2f}', f'{b.deposit:.2f}', f'{b.gateway_charge:.2f}',
                 f'{b.total:.2f}']
                for b in _booking_report_rows(request)[:5000]]

    if fmt == 'pdf':
        widths = [30, 46, 30, 24, 22, 24] if len(headers) == 6 else None
        return table_pdf(f'{report}-report.pdf', f'{report.title()} report',
                         headers, rows,
                         subtitle=f'Generated {timezone.localtime():%d %b %Y %H:%M} · sample data',
                         widths=widths,
                         footer_note='Demo version. Values are sample data.')
    return csv_response(f'{report}-report.csv', headers, rows)


@perm_required('mis.reports')
def report_library(request):
    reports = [
        {'code': 'bookings', 'title': 'Booking register', 'icon': 'calendar-check',
         'desc': 'Every application with status, dates, charges and payment totals.'},
        {'code': 'revenue', 'title': 'Revenue by month', 'icon': 'cash-stack',
         'desc': 'Verified collections per month for the last 12 months.'},
        {'code': 'workflow', 'title': 'Workflow register', 'icon': 'diagram-3',
         'desc': 'Instances, current status and completion dates.'},
        {'code': 'hr', 'title': 'Employee register', 'icon': 'people',
         'desc': 'Employee master list with department and designation.'},
        {'code': 'projects', 'title': 'Project register', 'icon': 'kanban',
         'desc': 'Budget, expenditure and progress by project.'},
    ]
    logs = []
    if request.user.can('mis.audit'):
        logs = ReportAccessLog.objects.select_related('user')[:12]
    return render(request, 'mis/reports.html', {
        'reports': reports, 'logs': logs,
        'can_export': request.user.can('mis.export'),
        'bookings': Booking.objects.count(),
        'payments': Payment.objects.filter(status='success').count(),
        'audit_entries': AuditEntry.objects.count(),
        'page_title': 'Report library',
    })


@perm_required('mis.audit')
def access_log(request):
    rows = ReportAccessLog.objects.select_related('user')[:400]
    return render(request, 'mis/access_log.html', {
        'rows': rows, 'page_title': 'Report access log',
    })
