import json
from collections import Counter
from datetime import timedelta

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import perm_required, staff_required
from audit.models import log
from core.models import get_int
from core.utils import human_duration, paginate, parse_date
from workflow import engine
from workflow.forms import StepForm, TemplateForm
from workflow.models import (
    AuthorityMatrix,
    StepRecord,
    WorkflowInstance,
    WorkflowStep,
    WorkflowTask,
    WorkflowTemplate,
)


@staff_required
def tasks(request):
    rows = WorkflowTask.objects.select_related(
        'instance', 'step', 'role', 'instance__requester'
    ).filter(Q(role=request.user.role) | Q(assignee=request.user))

    status = request.GET.get('status', 'open')
    priority = request.GET.get('priority', '')
    q = request.GET.get('q', '').strip()
    date_from = parse_date(request.GET.get('from'))
    date_to = parse_date(request.GET.get('to'))

    if status == 'open':
        rows = rows.filter(status='pending')
    elif status == 'completed':
        rows = rows.filter(status='completed')
    elif status == 'returned':
        rows = rows.filter(instance__status='returned')
    elif status == 'overdue':
        rows = rows.filter(status='pending', due_at__lt=timezone.now())
    if priority:
        rows = rows.filter(priority=priority)
    if q:
        rows = rows.filter(
            Q(instance__tracking_id__icontains=q) | Q(instance__payload__subject__icontains=q)
            | Q(step__name__icontains=q)
        )
    if date_from:
        rows = rows.filter(created_at__date__gte=date_from)
    if date_to:
        rows = rows.filter(created_at__date__lte=date_to)

    rows = rows.order_by('due_at')
    counts = {
        'open': WorkflowTask.objects.filter(
            Q(role=request.user.role) | Q(assignee=request.user), status='pending'
        ).count(),
        'overdue': WorkflowTask.objects.filter(
            Q(role=request.user.role) | Q(assignee=request.user),
            status='pending', due_at__lt=timezone.now()
        ).count(),
        'completed': WorkflowTask.objects.filter(
            Q(role=request.user.role) | Q(assignee=request.user), status='completed'
        ).count(),
    }
    return render(request, 'workflow/tasks.html', {
        'page_obj': paginate(request, rows, 25),
        'counts': counts, 'status': status, 'priority': priority, 'q': q,
        'page_title': 'My tasks',
    })


def _can_act(user, task):
    return bool(
        user.is_authenticated and user.role_id == task.role_id
        or user.can('workflow.manage')
    )


@staff_required
def task_detail(request, pk):
    task = get_object_or_404(
        WorkflowTask.objects.select_related(
            'instance', 'instance__template', 'step', 'role', 'instance__requester'
        ), pk=pk
    )
    if not _can_act(request.user, task) and task.assignee_id != request.user.pk:
        raise PermissionDenied('This task belongs to another role.')
    records = task.instance.records.select_related('actor', 'step')
    return render(request, 'workflow/task_detail.html', {
        'task': task,
        'instance': task.instance,
        'records': records,
        'allowed': task.step.decision_labels if task.status == 'pending' else [],
        'page_title': 'Task detail',
    })


@staff_required
def task_decide(request, pk):
    if request.method != 'POST':
        return redirect('tasks')
    task = get_object_or_404(WorkflowTask.objects.select_related('instance'), pk=pk)
    if not _can_act(request.user, task):
        raise PermissionDenied('This task belongs to another role.')
    decision = request.POST.get('decision', '')
    comments = request.POST.get('comments', '').strip()
    if not comments:
        messages.error(request, 'Add a short note with your decision.')
        return redirect('task_detail', pk=task.pk)
    try:
        ok, message = engine.decide(task, request.user, decision, comments)
    except PermissionDenied:
        raise
    except ValidationError as exc:
        ok, message = False, exc.messages[0]
    if ok:
        messages.success(request, message)
    else:
        messages.error(request, message)
    instance = task.instance
    url = instance.payload.get('url')
    if url and ok:
        return redirect(url)
    return redirect('task_detail', pk=task.pk)


@perm_required('workflow.manage')
def templates_list(request):
    templates = WorkflowTemplate.objects.prefetch_related('steps__role').all()
    return render(request, 'workflow/templates.html', {
        'templates': templates, 'page_title': 'Workflow designer',
    })


@perm_required('workflow.manage')
def template_form(request, pk=None):
    template = get_object_or_404(WorkflowTemplate, pk=pk) if pk else None
    if request.method == 'POST':
        form = TemplateForm(request.POST, instance=template)
        if form.is_valid():
            saved = form.save()
            log(request.user, 'settings', saved, 'Workflow template saved', request,
                module='workflow')
            messages.success(request, 'Workflow template saved.')
            return redirect('workflow_templates')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = TemplateForm(instance=template)
    return render(request, 'workflow/template_form.html', {
        'form': form, 'template': template,
        'page_title': 'Workflow template',
    })


@perm_required('workflow.manage')
def step_form(request, template_pk, pk=None):
    template = get_object_or_404(WorkflowTemplate, pk=template_pk)
    step = get_object_or_404(WorkflowStep, pk=pk, template=template) if pk else None
    if request.method == 'POST':
        form = StepForm(request.POST, instance=step)
        if form.is_valid():
            saved = form.save(commit=False)
            saved.template = template
            condition = form.cleaned_data.get('condition_text', '').strip()
            if condition:
                try:
                    saved.condition = json.loads(condition)
                except json.JSONDecodeError as exc:
                    form.add_error('condition_text', f'Invalid JSON: {exc}')
                    return render(request, 'workflow/step_form.html', {
                        'form': form, 'template': template, 'step': step,
                        'page_title': 'Workflow step',
                    })
            else:
                saved.condition = None
            try:
                saved.save()
            except Exception:
                messages.error(
                    request,
                    'Could not save the step. Check that the order number is unique '
                    'within this template.',
                )
                return render(request, 'workflow/step_form.html', {
                    'form': form, 'template': template, 'step': step,
                    'page_title': 'Workflow step',
                })
            log(request.user, 'settings', saved, 'Workflow step saved', request,
                module='workflow')
            messages.success(request, 'Workflow step saved.')
            return redirect('workflow_templates')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = StepForm(instance=step, initial={
            'condition_text': json.dumps(step.condition, indent=2) if step and step.condition else '',
        })
    return render(request, 'workflow/step_form.html', {
        'form': form, 'template': template, 'step': step,
        'page_title': 'Workflow step',
    })


@perm_required('workflow.manage')
def step_delete(request, pk):
    step = get_object_or_404(WorkflowStep, pk=pk)
    if request.method == 'POST':
        template = step.template
        log(request.user, 'settings', step, 'Workflow step deleted', request,
            module='workflow')
        step.delete()
        messages.success(request, 'Step deleted.')
        return redirect('workflow_templates')
    return redirect('workflow_templates')


@perm_required('workflow.manage')
def matrix(request):
    rows = AuthorityMatrix.objects.select_related('role').all()
    if request.method == 'POST':
        role_code = request.POST.get('role')
        category = request.POST.get('category')
        row = AuthorityMatrix.objects.filter(
            role__code=role_code, category=category
        ).first()
        if row is None:
            row = AuthorityMatrix(role_id=None)
            from accounts.models import Role
            role = Role.objects.filter(code=role_code).first()
            if role is None:
                messages.error(request, 'Choose a valid role.')
                return redirect('authority_matrix')
            row.role = role
        row.category = category
        row.can_approve = bool(request.POST.get('can_approve'))
        max_amount = request.POST.get('max_amount', '').strip()
        row.max_amount = max_amount or None
        row.note = request.POST.get('note', '').strip()
        row.save()
        log(request.user, 'settings', row, 'Authority matrix updated', request,
            module='workflow')
        messages.success(request, 'Authority matrix updated.')
        return redirect('authority_matrix')

    grouped = {}
    for row in rows:
        grouped.setdefault(row.get_category_display(), []).append(row)
    from accounts.models import Role
    return render(request, 'workflow/matrix.html', {
        'rows': rows, 'grouped': grouped,
        'roles': Role.objects.all(),
        'categories': WorkflowTemplate.CATEGORIES,
        'page_title': 'Authority matrix',
    })


@perm_required('workflow.manage')
def matrix_delete(request, pk):
    row = get_object_or_404(AuthorityMatrix, pk=pk)
    if request.method == 'POST':
        log(request.user, 'settings', row, 'Authority matrix row removed', request,
            module='workflow')
        row.delete()
        messages.success(request, 'Authority row removed.')
    return redirect('authority_matrix')


@staff_required
def run_reminders_now(request):
    if request.method != 'POST':
        return redirect('tasks')
    if not (request.user.can('workflow.run_reminders') or request.user.can('workflow.manage')):
        raise PermissionDenied('You cannot run reminders.')
    result = engine.run_reminders(
        request.user,
        reminder_hours=get_int('reminder_hours', 6),
        escalation_hours=get_int('escalation_hours', 12),
    )
    messages.success(
        request,
        f'Reminders run: {result["reminders"]} reminder(s), '
        f'{result["escalations"]} escalation(s).',
    )
    return redirect(request.META.get('HTTP_REFERER') or '/app/tasks/')


@perm_required('workflow.audit', 'mis.reports')
def performance(request):
    qs = WorkflowInstance.objects.select_related('template', 'requester')
    category = request.GET.get('category', '')
    date_from = parse_date(request.GET.get('from'))
    date_to = parse_date(request.GET.get('to'))
    if category:
        qs = qs.filter(template__category=category)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    instances = list(qs[:1000])
    counts = Counter(i.status for i in instances)
    completed = [i for i in instances if i.completed_at]
    durations = [(i.completed_at - i.created_at).total_seconds() for i in completed]
    avg_turnaround = timedelta(seconds=sum(durations) / len(durations)) if durations else None
    open_tasks = WorkflowTask.objects.filter(status='pending')
    overdue = open_tasks.filter(due_at__lt=timezone.now())
    rejections = StepRecord.objects.filter(decision='reject').select_related('instance')
    reasons = Counter()
    for record in rejections[:200]:
        reasons[(record.comments or 'No reason recorded')[:90]] += 1
    by_template = (
        qs.values('template__name', 'template__category')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    by_step = (
        open_tasks.values('step__name', 'role__name')
        .annotate(total=Count('id'))
        .order_by('-total')[:8]
    )
    return render(request, 'workflow/performance.html', {
        'page_title': 'Workflow performance',
        'instances': instances[:15],
        'counts': sorted(counts.items()),
        'open_count': open_tasks.count(),
        'overdue_count': overdue.count(),
        'avg_turnaround': human_duration(avg_turnaround) if avg_turnaround else '-',
        'reasons': reasons.most_common(6),
        'by_template': by_template,
        'by_step': by_step,
        'category': category,
        'categories': WorkflowTemplate.CATEGORIES,
        'total': len(instances),
    })


@perm_required('workflow.view')
def instance_detail(request, pk):
    instance = get_object_or_404(
        WorkflowInstance.objects.select_related('template', 'requester'), pk=pk)
    return render(request, 'workflow/instance_detail.html', {
        'instance': instance,
        'records': instance.records.select_related('actor', 'step'),
        'tasks': instance.tasks.select_related('step', 'role', 'assignee'),
        'steps': engine.applicable_steps(instance.template, instance.payload),
        'page_title': f'Workflow {instance.tracking_id}',
    })
