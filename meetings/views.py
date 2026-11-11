from __future__ import annotations

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import perm_required
from accounts.models import User
from audit.models import log
from core.utils import paginate, parse_date, today
from meetings.models import ActionItem, Attendee, Meeting


@perm_required('meetings.view')
def meeting_list(request):
    rows = Meeting.objects.select_related('chair', 'secretary').order_by(
        '-date', '-start_time', 'pk')
    status = request.GET.get('status', '')
    if status:
        rows = rows.filter(status=status)
    if request.method == 'POST':
        if not request.user.can('meetings.manage'):
            raise PermissionDenied('You cannot schedule meetings.')
        title = request.POST.get('title', '').strip()
        day = parse_date(request.POST.get('date'))
        if not title or not day:
            messages.error(request, 'Title and date are required.')
        else:
            meeting = Meeting.objects.create(
                title=title, date=day, venue=request.POST.get('venue', '').strip(),
                agenda=request.POST.get('agenda', '').strip(),
                chair=User.objects.filter(pk=request.POST.get('chair')).first(),
                secretary=request.user,
            )
            log(request.user, 'create', meeting, f'Meeting scheduled: {title}', request,
                module='meetings')
            messages.success(request, 'Meeting scheduled.')
        return redirect('meetings_list')

    return render(request, 'meetings/list.html', {
        'page_obj': paginate(request, rows),
        'statuses': Meeting.STATUS,
        'users': User.objects.filter(is_active=True, role__isnull=False).select_related('role'),
        'today': today(),
        'status': status,
        'open_actions': ActionItem.objects.exclude(status__in=('done', 'cancelled')).count(),
        'page_title': 'Meetings',
    })


@perm_required('meetings.view')
def meeting_detail(request, pk):
    meeting = get_object_or_404(
        Meeting.objects.select_related('chair', 'secretary'), pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'minutes':
            if not request.user.can('meetings.minutes'):
                raise PermissionDenied('You cannot record minutes.')
            meeting.minutes = request.POST.get('minutes', '').strip()
            meeting.status = request.POST.get('status', meeting.status)
            meeting.save(update_fields=['minutes', 'status'])
            log(request.user, 'update', meeting, 'Minutes updated', request, module='meetings')
            messages.success(request, 'Minutes saved.')
        elif action == 'attendee':
            if not request.user.can('meetings.manage'):
                raise PermissionDenied('You cannot edit attendees.')
            user = User.objects.filter(pk=request.POST.get('user')).first()
            name = request.POST.get('name', '').strip() or (user.display_name if user else '')
            if name:
                Attendee.objects.get_or_create(
                    meeting=meeting, name=name,
                    defaults={'user': user, 'role': request.POST.get('role', '').strip()},
                )
                messages.success(request, 'Attendee added.')
        elif action == 'presence':
            if not request.user.can('meetings.minutes'):
                raise PermissionDenied('You cannot record attendance.')
            attendee = get_object_or_404(Attendee, pk=request.POST.get('attendee'),
                                         meeting=meeting)
            attendee.present = not attendee.present
            attendee.save(update_fields=['present'])
        elif action == 'action':
            if not request.user.can('meetings.minutes') and not request.user.can('meetings.manage'):
                raise PermissionDenied('You cannot assign actions.')
            description = request.POST.get('description', '').strip()
            if description:
                ActionItem.objects.create(
                    meeting=meeting, description=description,
                    owner=User.objects.filter(pk=request.POST.get('owner')).first(),
                    owner_label=request.POST.get('owner_label', '').strip(),
                    due_date=parse_date(request.POST.get('due_date')),
                )
                messages.success(request, 'Action item assigned.')
            else:
                messages.error(request, 'Action description is required.')
        return redirect('meetings_detail', pk=meeting.pk)

    return render(request, 'meetings/detail.html', {
        'meeting': meeting,
        'attendees': meeting.attendees.all(),
        'actions': meeting.actions.select_related('owner'),
        'users': User.objects.filter(is_active=True, role__isnull=False).select_related('role'),
        'statuses': Meeting.STATUS,
        'page_title': meeting.title,
    })


@perm_required('meetings.view')
def actions(request):
    rows = ActionItem.objects.select_related('meeting', 'owner')
    status = request.GET.get('status', 'open')
    if status == 'open':
        rows = rows.exclude(status__in=('done', 'cancelled'))
    elif status == 'overdue':
        rows = [a for a in rows if a.is_overdue]
    elif status:
        rows = rows.filter(status=status)

    if request.method == 'POST':
        if not request.user.can('meetings.action'):
            raise PermissionDenied('You cannot update actions.')
        item = get_object_or_404(ActionItem, pk=request.POST.get('action_id'))
        new_status = request.POST.get('status', 'open')
        item.status = new_status
        item.note = request.POST.get('note', item.note).strip()
        if new_status == 'done':
            item.completed_at = timezone.now()
        item.save()
        log(request.user, 'update', item, f'Action {new_status}', request, module='meetings')
        messages.success(request, 'Action item updated.')
        return redirect('meetings_actions')

    page_obj = paginate(request, rows)
    return render(request, 'meetings/actions.html', {
        'rows': page_obj,
        'page_obj': page_obj,
        'status': status,
        'statuses': ActionItem.STATUS,
        'page_title': 'Action follow-up',
    })
