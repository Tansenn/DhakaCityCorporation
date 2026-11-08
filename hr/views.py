from __future__ import annotations

from datetime import timedelta

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import perm_required, staff_required
from audit.models import log
from core.utils import parse_date, today
from hr.models import (
    Attendance,
    Department,
    Designation,
    Employee,
    LeaveRequest,
    Roster,
    TrainingRecord,
)
from workflow import engine
from workflow.models import WorkflowTemplate


def _employee_for(user):
    return Employee.objects.filter(user=user).first()


@perm_required('hr.view', 'hr.self')
def dashboard(request):
    employees = Employee.objects.select_related('department', 'designation')
    department = request.GET.get('department', '')
    if department:
        employees = employees.filter(department__code=department)
    stats = {
        'total': Employee.objects.count(),
        'active': Employee.objects.filter(status='active').count(),
        'on_leave': Employee.objects.filter(status='leave').count(),
        'departments': Department.objects.count(),
    }
    upcoming_leave = LeaveRequest.objects.filter(
        status__in=('approved', 'recommended'), start_date__gte=today()
    ).select_related('employee')[:6]
    expiring = TrainingRecord.objects.filter(
        expires_on__lte=today() + timedelta(days=60)
    ).select_related('employee')[:6]
    return render(request, 'hr/dashboard.html', {
        'stats': stats,
        'employees': employees[:8],
        'departments': Department.objects.all(),
        'selected_department': department,
        'upcoming_leave': upcoming_leave,
        'expiring': expiring,
        'page_title': 'Human resources',
    })


@perm_required('hr.view')
def employees(request):
    rows = Employee.objects.select_related('department', 'designation', 'supervisor')
    q = request.GET.get('q', '').strip()
    department = request.GET.get('department', '')
    status = request.GET.get('status', '')
    if q:
        rows = rows.filter(Q(name__icontains=q) | Q(employee_no__icontains=q)
                           | Q(designation__name__icontains=q))
    if department:
        rows = rows.filter(department__code=department)
    if status:
        rows = rows.filter(status=status)

    if request.method == 'POST':
        if not request.user.can('hr.manage'):
            raise PermissionDenied('You cannot add employees.')
        employee_no = request.POST.get('employee_no', '').strip()
        name = request.POST.get('name', '').strip()
        if not employee_no or not name:
            messages.error(request, 'Employee number and name are required.')
        elif Employee.objects.filter(employee_no__iexact=employee_no).exists():
            messages.error(request, 'That employee number already exists.')
        else:
            department_obj = Department.objects.filter(
                pk=request.POST.get('department')).first()
            designation_obj = Designation.objects.filter(
                pk=request.POST.get('designation')).first()
            employee = Employee.objects.create(
                employee_no=employee_no, name=name,
                department=department_obj, designation=designation_obj,
                joining_date=parse_date(request.POST.get('joining_date')),
                employment_type=request.POST.get('employment_type', 'permanent'),
                phone=request.POST.get('phone', '').strip(),
                email=request.POST.get('email', '').strip(),
            )
            log(request.user, 'create', employee, f'Employee {employee.employee_no} added',
                request, module='hr')
            messages.success(request, f'Employee {employee.employee_no} added.')
            return redirect('hr_employees')

    return render(request, 'hr/employees.html', {
        'page_obj': rows,
        'departments': Department.objects.all(),
        'designations': Designation.objects.select_related('department').all(),
        'q': q, 'department': department, 'status': status,
        'page_title': 'Employees',
    })


@perm_required('hr.view', 'hr.self')
def employee_detail(request, pk):
    employee = get_object_or_404(
        Employee.objects.select_related('department', 'designation', 'supervisor'), pk=pk)
    if not request.user.can('hr.view') and employee.user_id != request.user.pk:
        raise PermissionDenied('You can only view your own employee record.')
    return render(request, 'hr/employee_detail.html', {
        'employee': employee,
        'attendance': employee.attendance.order_by('-date')[:10],
        'leaves': employee.leaves.order_by('-applied_at')[:8],
        'training': employee.training.all(),
        'page_title': employee.name,
    })


@perm_required('hr.attendance')
def attendance(request):
    day = parse_date(request.GET.get('date')) or today()
    employees = Employee.objects.filter(status__in=('active', 'leave')).select_related(
        'department')
    records = {a.employee_id: a for a in Attendance.objects.filter(date=day)}
    if request.method == 'POST':
        day = parse_date(request.POST.get('date')) or day
        saved = 0
        for employee in employees:
            status = request.POST.get(f'status_{employee.pk}')
            if not status:
                continue
            Attendance.objects.update_or_create(
                employee=employee, date=day,
                defaults={'status': status, 'recorded_by': request.user},
            )
            saved += 1
        log(request.user, 'update', None, f'Attendance marked for {saved} employee(s) on {day}',
            request, module='hr')
        messages.success(request, f'Attendance saved for {saved} employee(s) on {day}.')
        return redirect(f'/app/hr/attendance/?date={day:%Y-%m-%d}')

    counts = {}
    for status, _ in Attendance.STATUS:
        counts[status] = sum(1 for r in records.values() if r.status == status)
    return render(request, 'hr/attendance.html', {
        'day': day, 'employees': employees, 'records': records,
        'statuses': Attendance.STATUS, 'counts': counts,
        'page_title': 'Attendance',
    })


@perm_required('hr.self', 'hr.view')
def leave(request):
    employee = _employee_for(request.user)
    can_see_all = request.user.can('hr.view') or request.user.can('hr.leave_hr')
    rows = LeaveRequest.objects.select_related('employee', 'employee__department')
    if not can_see_all:
        rows = rows.filter(employee=employee) if employee else rows.none()
    status = request.GET.get('status', '')
    if status:
        rows = rows.filter(status=status)

    if request.method == 'POST':
        if employee is None:
            messages.error(request, 'Your account is not linked to an employee record.')
            return redirect('hr_leave')
        leave_type = request.POST.get('leave_type', 'casual')
        start = parse_date(request.POST.get('start_date'))
        end = parse_date(request.POST.get('end_date')) or start
        reason = request.POST.get('reason', '').strip()
        if not start or not reason:
            messages.error(request, 'Start date and reason are required.')
        elif end < start:
            messages.error(request, 'The end date cannot be before the start date.')
        else:
            leave_obj = LeaveRequest.objects.create(
                employee=employee, leave_type=leave_type,
                start_date=start, end_date=end, reason=reason,
            )
            template = WorkflowTemplate.objects.filter(
                code='leave-application', is_active=True).first()
            if template:
                engine.start(template, leave_obj, {
                    'subject': f'Leave: {employee.name}',
                    'applicant': employee.name,
                    'leave_type': leave_type,
                    'days': leave_obj.days,
                    'amount': 0,
                    'url': f'/app/hr/leave/',
                }, request.user, note=reason)
            else:
                messages.warning(request, 'Leave saved, but no leave workflow template is active.')
            log(request.user, 'create', leave_obj, f'Leave request {start} to {end}', request,
                module='hr')
            messages.success(request, 'Leave application submitted.')
        return redirect('hr_leave')

    return render(request, 'hr/leave.html', {
        'page_obj': rows,
        'employee': employee,
        'can_see_all': can_see_all,
        'leave_types': LeaveRequest.TYPES,
        'statuses': LeaveRequest.STATUS,
        'status': status,
        'page_title': 'Leave',
    })


@perm_required('hr.roster')
def roster(request):
    start = parse_date(request.GET.get('start')) or today()
    start = start - timedelta(days=start.weekday())
    days = [start + timedelta(days=i) for i in range(7)]
    if request.method == 'POST':
        employee = get_object_or_404(Employee, pk=request.POST.get('employee'))
        day = parse_date(request.POST.get('date'))
        shift = request.POST.get('shift', 'day')
        note = request.POST.get('note', '').strip()
        if not day:
            messages.error(request, 'Choose a date.')
        else:
            Roster.objects.update_or_create(
                employee=employee, date=day,
                defaults={'shift': shift, 'note': note},
            )
            log(request.user, 'update', employee, f'Roster {day} {shift}', request, module='hr')
            messages.success(request, f'Roster saved for {employee.name} on {day}.')
        return redirect(f'/app/hr/roster/?start={start:%Y-%m-%d}')

    rows = Roster.objects.filter(date__range=(days[0], days[-1])).select_related('employee')
    grid = {}
    for row in rows:
        grid.setdefault(row.employee_id, {})[row.date] = row
    employees = Employee.objects.filter(status='active')
    return render(request, 'hr/roster.html', {
        'days': days, 'employees': employees, 'grid': grid,
        'shifts': Roster.SHIFTS, 'start': start,
        'page_title': 'Duty roster',
    })


@perm_required('hr.training')
def training(request):
    rows = TrainingRecord.objects.select_related('employee')
    if request.method == 'POST':
        employee = get_object_or_404(Employee, pk=request.POST.get('employee'))
        title = request.POST.get('title', '').strip()
        if not title:
            messages.error(request, 'Training title is required.')
        else:
            record = TrainingRecord.objects.create(
                employee=employee, title=title,
                provider=request.POST.get('provider', '').strip(),
                completed_on=parse_date(request.POST.get('completed_on')),
                expires_on=parse_date(request.POST.get('expires_on')),
                note=request.POST.get('note', '').strip(),
            )
            log(request.user, 'create', record, 'Training record added', request, module='hr')
            messages.success(request, 'Training record added.')
        return redirect('hr_training')
    return render(request, 'hr/training.html', {
        'rows': rows,
        'employees': Employee.objects.filter(status='active'),
        'page_title': 'Training and expiry',
    })
