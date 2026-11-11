from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import perm_required
from accounts.models import User
from audit.models import log
from core.utils import business_hours_after, next_reference, paginate, parse_date
from support.models import ChangeRequest, ChecklistItem, PlanPhase, Ticket


@perm_required('support.view')
def tickets(request):
    rows = Ticket.objects.select_related('requester', 'assignee')
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    if status == 'open':
        rows = rows.exclude(status__in=('resolved', 'closed'))
    elif status:
        rows = rows.filter(status=status)
    if priority:
        rows = rows.filter(priority=priority)

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()
        if not subject or not description:
            messages.error(request, 'Subject and description are required.')
        else:
            priority_value = request.POST.get('priority', 'medium')
            hours = settings.SUPPORT_TARGETS.get(priority_value.title(), 8)
            ticket = Ticket.objects.create(
                number=next_reference('GZP-ST', Ticket, 'number', width=4),
                subject=subject, description=description,
                category=request.POST.get('category', 'incident'),
                priority=priority_value, requester=request.user,
                response_due_at=business_hours_after(timezone.now(), hours),
            )
            log(request.user, 'create', ticket, f'Ticket {ticket.number} created', request,
                module='support')
            messages.success(
                request,
                f'Ticket {ticket.number} logged. Response target: {hours} business hours.')
        return redirect('support_tickets')

    stats = {
        'open': Ticket.objects.exclude(status__in=('resolved', 'closed')).count(),
        'critical': Ticket.objects.exclude(status__in=('resolved', 'closed')).filter(
            priority='critical').count(),
        'overdue': sum(1 for t in Ticket.objects.exclude(
            status__in=('resolved', 'closed')) if t.is_overdue),
        'resolved': Ticket.objects.filter(status__in=('resolved', 'closed')).count(),
    }
    return render(request, 'support/tickets.html', {
        'page_obj': paginate(request, rows),
        'statuses': Ticket.STATUS,
        'priorities': Ticket.PRIORITY,
        'categories': Ticket.CATEGORIES,
        'targets': settings.SUPPORT_TARGETS,
        'stats': stats,
        'status': status, 'priority': priority,
        'page_title': 'Support tickets',
    })


@perm_required('support.view')
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket.objects.select_related('requester', 'assignee'), pk=pk)
    if request.method == 'POST':
        if not request.user.can('support.manage'):
            raise PermissionDenied('You cannot update tickets.')
        ticket.status = request.POST.get('status', ticket.status)
        ticket.assignee = User.objects.filter(pk=request.POST.get('assignee')).first()
        resolution = request.POST.get('resolution', '').strip()
        if resolution:
            ticket.resolution = resolution
        if ticket.status == 'resolved' and not ticket.resolved_at:
            ticket.resolved_at = timezone.now()
        ticket.save()
        log(request.user, 'update', ticket, f'Ticket {ticket.number} -> {ticket.status}',
            request, module='support')
        messages.success(request, 'Ticket updated.')
        return redirect('support_ticket', pk=ticket.pk)
    return render(request, 'support/ticket_detail.html', {
        'ticket': ticket,
        'statuses': Ticket.STATUS,
        'users': User.objects.filter(is_active=True, role__isnull=False).select_related('role'),
        'page_title': ticket.number,
    })


@perm_required('support.view')
def acceptance(request):
    phases = PlanPhase.objects.order_by('sort_order', 'pk')
    if request.method == 'POST':
        if not request.user.can('support.manage'):
            raise PermissionDenied('You cannot edit the plan.')
        phase = get_object_or_404(PlanPhase, pk=request.POST.get('phase'))
        phase.status = request.POST.get('status', phase.status)
        phase.notes = request.POST.get('notes', phase.notes).strip()
        phase.save(update_fields=['status', 'notes'])
        messages.success(request, 'Plan updated.')
        return redirect('support_acceptance')
    done = phases.filter(status='done').count()
    total = phases.count()
    page_obj = paginate(request, phases)
    return render(request, 'support/acceptance.html', {
        'phases': page_obj,
        'page_obj': page_obj,
        'statuses': PlanPhase.STATUS,
        'done': done,
        'total': total,
        'percent': round(done / total * 100) if total else 0,
        'page_title': '45-day plan',
    })


@perm_required('support.view')
def checklists(request):
    kind = request.GET.get('kind', '')
    rows = ChecklistItem.objects.order_by('kind', 'sort_order', 'pk')
    if kind:
        rows = rows.filter(kind=kind)
    if request.method == 'POST':
        if not request.user.can('support.uat'):
            raise PermissionDenied('You cannot record UAT results.')
        item = get_object_or_404(ChecklistItem, pk=request.POST.get('item'))
        item.status = request.POST.get('status', item.status)
        item.note = request.POST.get('note', item.note).strip()
        item.checked_by = request.user
        item.checked_at = timezone.now()
        item.save()
        log(request.user, 'update', item, f'Checklist {item.status}', request, module='support')
        messages.success(request, 'Checklist updated.')
        return redirect(f'/app/acceptance/checklists/?kind={kind}' if kind
                        else '/app/acceptance/checklists/')
    passed = rows.filter(status='passed').count()
    page_obj = paginate(request, rows)
    return render(request, 'support/checklists.html', {
        'rows': page_obj, 'page_obj': page_obj, 'kind': kind, 'passed': passed,
        'statuses': ChecklistItem.STATUS,
        'kinds': ChecklistItem.KINDS,
        'page_title': 'Deliverables and UAT',
    })


@perm_required('support.view')
def change_requests(request):
    rows = ChangeRequest.objects.select_related('requested_by')
    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        if action == 'create':
            if not request.user.can('support.change'):
                raise PermissionDenied('You cannot submit change requests.')
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            if not title or not description:
                messages.error(request, 'Title and description are required.')
            else:
                change = ChangeRequest.objects.create(
                    reference=next_reference('GZP-CR', ChangeRequest, 'reference', width=3),
                    title=title, description=description,
                    impact=request.POST.get('impact', 'medium'),
                    requested_by=request.user,
                )
                log(request.user, 'create', change, f'Change request {change.reference}',
                    request, module='support')
                messages.success(request, 'Change request submitted.')
        else:
            if not request.user.can('support.manage'):
                raise PermissionDenied('You cannot decide change requests.')
            change = get_object_or_404(ChangeRequest, pk=request.POST.get('id'))
            change.status = request.POST.get('status', change.status)
            change.decision_note = request.POST.get('decision_note', '').strip()
            change.decided_at = timezone.now()
            change.save()
            log(request.user, 'update', change,
                f'Change request {change.reference} -> {change.status}', request,
                module='support')
            messages.success(request, 'Change request updated.')
        return redirect('support_changes')
    page_obj = paginate(request, rows)
    return render(request, 'support/change_requests.html', {
        'rows': page_obj,
        'page_obj': page_obj,
        'statuses': ChangeRequest.STATUS,
        'impacts': ChangeRequest.IMPACT,
        'page_title': 'Change requests',
    })
