"""Database-driven workflow engine.

Routes come from WorkflowStep rows (role + condition + allowed decisions) and
approval authority comes from AuthorityMatrix. Nothing about the route is
hard-coded in the module views.
"""
from __future__ import annotations

from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from audit.models import log
from notifications.services import send
from workflow.models import (
    AuthorityMatrix,
    StepRecord,
    WorkflowInstance,
    WorkflowStep,
    WorkflowTask,
    WorkflowTemplate,
)

DECISION_LABELS = {
    'forward': 'Reviewed and forwarded',
    'recommend': 'Recommended',
    'approve': 'Approved',
    'reject': 'Rejected',
    'correct': 'Correction requested',
    'return': 'Returned for correction',
    'submit': 'Submitted',
}

TRACKING_PREFIX = {
    'booking': 'GZP-DB', 'leave': 'GZP-LV', 'file': 'GZP-FL', 'project': 'GZP-PA',
}


def condition_matches(condition, payload):
    """Evaluate the small condition DSL used by step configuration."""
    if not condition:
        return True
    if not isinstance(condition, dict):
        return True
    if 'any' in condition:
        return any(condition_matches(c, payload) for c in condition['any'])
    if 'all' in condition:
        return all(condition_matches(c, payload) for c in condition['all'])
    for key, expected in condition.items():
        if key.startswith('min_'):
            field = key[4:]
            try:
                if float(payload.get(field) or 0) < float(expected):
                    return False
            except (TypeError, ValueError):
                return False
        elif key.startswith('max_'):
            field = key[4:]
            try:
                if float(payload.get(field) or 0) > float(expected):
                    return False
            except (TypeError, ValueError):
                return False
        else:
            actual = payload.get(key)
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False
    return True


def applicable_steps(template, payload):
    payload = payload or {}
    return [
        step for step in template.steps.select_related('role').order_by('order')
        if condition_matches(step.condition, payload)
    ]


def _next_task(instance, step, priority='normal'):
    due = timezone.now() + timedelta(hours=step.sla_hours or 24)
    return WorkflowTask.objects.create(
        instance=instance,
        step=step,
        role=step.role,
        priority=priority,
        due_at=due,
    )


def _notify_role(step, instance, task):
    users = User.objects.filter(role=step.role, is_active=True)
    url = instance.payload.get('url') or f'/app/tasks/{task.pk}/'
    for user in users:
        send(
            user,
            'task_assigned',
            {
                'reference': instance.tracking_id,
                'subject': instance.subject,
                'step': step.name,
                'due': task.due_at.strftime('%d %b %Y %H:%M'),
            },
            url=f'/app/tasks/{task.pk}/',
            channels=['inapp'],
        )


def _notify_requester(instance, template_code, message):
    if not instance.requester:
        return
    send(
        instance.requester,
        template_code,
        {
            'reference': instance.tracking_id,
            'subject': instance.subject,
            'message': message,
            'status': instance.get_status_display(),
        },
        url=instance.payload.get('url', ''),
        channels=['inapp', 'email', 'sms'],
    )


def _next_tracking(prefix):
    year = timezone.localdate().year
    base = f'{prefix}-{year}-'
    count = WorkflowInstance.objects.filter(tracking_id__startswith=base).count() + 1
    while WorkflowInstance.objects.filter(tracking_id=f'{base}{count:06d}').exists():
        count += 1
    return f'{base}{count:06d}'


@transaction.atomic
def start(template, obj, payload, requester, tracking_id=None, note='',
          priority='normal'):
    """Create an instance, resolve the route from the matrix and open the first task."""
    if isinstance(template, str):
        template = WorkflowTemplate.objects.get(code=template, is_active=True)
    if not template.is_active:
        raise ValidationError('This workflow template is not active.')

    payload = dict(payload or {})
    payload.setdefault('tracking_id', tracking_id or '')
    prefix = TRACKING_PREFIX.get(template.category, 'GZP-WF')
    instance = WorkflowInstance.objects.create(
        template=template,
        object_type=obj._meta.label,
        object_id=obj.pk,
        tracking_id=tracking_id or _next_tracking(prefix),
        requester=requester if getattr(requester, 'is_authenticated', False) else None,
        payload=payload,
        note=note,
    )
    StepRecord.objects.create(
        instance=instance, actor=instance.requester,
        actor_role=instance.requester.role.code if instance.requester and instance.requester.role else '',
        decision='submit', comments=note or 'Request submitted',
    )
    steps = applicable_steps(template, payload)
    if not steps:
        instance.status = 'approved'
        instance.completed_at = timezone.now()
        instance.save(update_fields=['status', 'completed_at'])
        log(instance.requester, 'decision', obj, f'{instance.tracking_id} auto-approved: no steps', module=template.category)
        _callback(instance, 'approve')
        return instance

    instance.current_step = steps[0]
    instance.save(update_fields=['current_step'])
    task = _next_task(instance, steps[0], priority)
    _notify_role(steps[0], instance, task)
    log(instance.requester, 'create', obj,
        f'Workflow {instance.tracking_id} started at {steps[0].name}', module=template.category)
    return instance


def _callback(instance, decision):
    obj = instance.object
    if obj is not None and hasattr(obj, 'on_workflow_decision'):
        obj.on_workflow_decision(decision, instance)
    return obj


def _authority_allows(role, category, amount):
    row = AuthorityMatrix.objects.filter(role=role, category=category).first()
    if row is None:
        return False, 'No authority matrix row is configured for this role and category.'
    if not row.can_approve:
        return False, f'{role.name} is not authorised to give final approval in this category.'
    if row.max_amount is not None and amount and float(amount) > float(row.max_amount):
        return False, (
            f'{role.name} may approve up to ৳{row.max_amount:,.2f}; '
            f'this request is ৳{float(amount):,.2f}.'
        )
    return True, ''


@transaction.atomic
def decide(task, user, decision, comments=''):
    """Apply a decision to a task. All checks happen on the server."""
    task = WorkflowTask.objects.select_related(
        'instance', 'step', 'role', 'instance__template'
    ).select_for_update().get(pk=task.pk)

    if task.status != 'pending':
        return False, 'This task is no longer pending.'
    if not user.role or user.role_id != task.role_id:
        raise PermissionDenied('This task is assigned to a different role.')
    if decision not in (task.step.allowed_decisions or []):
        return False, f'"{decision}" is not an allowed decision at the {task.step.name} step.'

    instance = task.instance
    if instance.status != 'running':
        return False, 'This workflow is not running.'

    if decision == 'approve':
        ok, reason = _authority_allows(task.role, instance.template.category,
                                       instance.amount)
        if not ok:
            return False, reason

    task.status = 'completed'
    task.completed_at = timezone.now()
    task.save(update_fields=['status', 'completed_at'])

    record = StepRecord.objects.create(
        instance=instance,
        step=task.step,
        task=task,
        actor=user,
        actor_role=user.role.code if user.role else '',
        decision=decision,
        comments=comments,
    )
    log(user, 'decision', instance.object or instance,
        f'{instance.tracking_id} {task.step.name}: {DECISION_LABELS.get(decision, decision)} - {comments}',
        module=instance.template.category)

    if decision in ('correct', 'return'):
        instance.status = 'returned'
        instance.note = comments[:255]
        instance.save(update_fields=['status', 'note'])
        _notify_requester(
            instance, 'clarification',
            f'{task.step.name} requested a correction: {comments}',
        )
        _callback(instance, decision)
        return True, 'Correction requested. The requester has been notified.'

    if decision == 'reject':
        instance.status = 'rejected'
        instance.completed_at = timezone.now()
        instance.current_step = None
        instance.note = comments[:255]
        instance.save(update_fields=['status', 'completed_at', 'current_step', 'note'])
        _notify_requester(
            instance, 'rejection',
            f'Your request was rejected at {task.step.name}: {comments}',
        )
        _callback(instance, 'reject')
        return True, 'Request rejected and the requester notified.'

    # forward / recommend / approve -> advance
    steps = applicable_steps(instance.template, instance.payload)
    try:
        index = [s.pk for s in steps].index(task.step_id)
    except ValueError:
        index = -1
    next_step = steps[index + 1] if index + 1 < len(steps) else None

    if next_step is None:
        instance.status = 'approved'
        instance.completed_at = timezone.now()
        instance.current_step = None
        instance.note = comments[:255]
        instance.save(update_fields=['status', 'completed_at', 'current_step', 'note'])
        _notify_requester(
            instance, 'approval',
            f'Your request was approved at {task.step.name}. {comments}',
        )
        _callback(instance, 'approve')
        return True, 'Final approval recorded.'

    instance.status = 'running'
    instance.current_step = next_step
    instance.save(update_fields=['status', 'current_step'])
    new_task = _next_task(instance, next_step, task.priority)
    _notify_role(next_step, instance, new_task)
    _notify_requester(
        instance, 'status_update',
        f'{task.step.name}: {DECISION_LABELS.get(decision, decision)}. '
        f'Next step: {next_step.name}.',
    )
    _callback(instance, decision)
    return True, f'Decision recorded. Forwarded to {next_step.name}.'


@transaction.atomic
def resume(instance, user, note=''):
    """Re-open a returned workflow at the step that asked for a correction."""
    if instance.status != 'returned':
        return None
    step = instance.current_step or applicable_steps(instance.template, instance.payload)[0]
    instance.status = 'running'
    instance.note = ''
    instance.current_step = step
    instance.save(update_fields=['status', 'current_step', 'note'])
    task = _next_task(instance, step, 'high')
    StepRecord.objects.create(
        instance=instance, step=step, actor=user,
        actor_role=user.role.code if user and user.role else '',
        decision='submit', comments=note or 'Requester responded to the correction request.',
    )
    _notify_role(step, instance, task)
    if instance.requester:
        send(instance.requester, 'status_update',
             {'reference': instance.tracking_id, 'subject': instance.subject,
              'message': 'Your response was received and the request is back under review.',
              'status': instance.get_status_display()},
             url=instance.payload.get('url', ''), channels=['inapp'])
    return task


def run_reminders(actor=None, reminder_hours=6, escalation_hours=12):
    """Send reminders before the due time and escalate overdue tasks to the
    nominated supervisor role. Configurable via settings."""
    now = timezone.now()
    reminders = 0
    escalations = 0
    upcoming = WorkflowTask.objects.filter(
        status='pending', reminder_sent_at__isnull=True,
        due_at__lte=now + timedelta(hours=reminder_hours),
    ).select_related('instance', 'step', 'role')
    for task in upcoming:
        for user in User.objects.filter(role=task.role, is_active=True):
            send(user, 'reminder',
                 {'reference': task.instance.tracking_id,
                  'subject': task.instance.subject,
                  'step': task.step.name,
                  'due': task.due_at.strftime('%d %b %Y %H:%M')},
                 url=f'/app/tasks/{task.pk}/', channels=['inapp'])
        task.reminder_sent_at = now
        task.save(update_fields=['reminder_sent_at'])
        reminders += 1

    supervisors = list(User.objects.filter(role__code='supervisor', is_active=True))
    if not supervisors:
        supervisors = list(User.objects.filter(role__code='admin', is_active=True)[:1])
    overdue = WorkflowTask.objects.filter(
        status='pending', escalated_at__isnull=True,
        due_at__lt=now - timedelta(hours=escalation_hours),
    ).select_related('instance', 'step', 'role')
    for task in overdue:
        supervisor = supervisors[0] if supervisors else None
        task.escalated_at = now
        task.escalated_to = supervisor
        task.save(update_fields=['escalated_at', 'escalated_to'])
        for user in supervisors:
            send(user, 'escalation',
                 {'reference': task.instance.tracking_id,
                  'subject': task.instance.subject,
                  'step': task.step.name,
                  'due': task.due_at.strftime('%d %b %Y %H:%M')},
                 url=f'/app/tasks/{task.pk}/', channels=['inapp'])
        escalations += 1

    log(actor, 'update', None,
        f'Reminders run: {reminders} reminders, {escalations} escalations',
        module='workflow')
    return {'reminders': reminders, 'escalations': escalations}
