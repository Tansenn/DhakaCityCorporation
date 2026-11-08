from __future__ import annotations

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import perm_required
from audit.models import log
from core.utils import next_reference, parse_date, parse_decimal, paginate
from hr.models import Department
from projects.models import Inspection, Milestone, Project


@perm_required('projects.view')
def project_list(request):
    rows = Project.objects.select_related('department', 'manager')
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    if q:
        rows = rows.filter(Q(name__icontains=q) | Q(code__icontains=q)
                           | Q(location__icontains=q))
    if status:
        rows = rows.filter(status=status)

    if request.method == 'POST':
        if not request.user.can('projects.manage'):
            raise PermissionDenied('You cannot create projects.')
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Project name is required.')
        else:
            project = Project.objects.create(
                code=next_reference('GZP-PR', Project, 'code', width=3),
                name=name,
                department=Department.objects.filter(
                    pk=request.POST.get('department')).first(),
                description=request.POST.get('description', '').strip(),
                location=request.POST.get('location', '').strip(),
                budget=parse_decimal(request.POST.get('budget')),
                start_date=parse_date(request.POST.get('start_date')),
                end_date=parse_date(request.POST.get('end_date')),
                status='planning',
                manager=request.user,
            )
            log(request.user, 'create', project, f'Project {project.code} created', request,
                module='projects')
            messages.success(request, f'Project {project.code} created.')
        return redirect('projects_list')

    totals = Project.objects.aggregate(budget=Sum('budget'), spent=Sum('spent'))
    stats = {
        'total': Project.objects.count(),
        'ongoing': Project.objects.filter(status='ongoing').count(),
        'delayed': Project.objects.filter(status='delayed').count(),
        'budget': totals['budget'] or 0,
        'spent': totals['spent'] or 0,
    }
    return render(request, 'projects/list.html', {
        'page_obj': paginate(request, rows, 20),
        'statuses': Project.STATUS,
        'departments': Department.objects.all(),
        'stats': stats,
        'q': q, 'status': status,
        'page_title': 'Projects',
    })


@perm_required('projects.view')
def project_detail(request, pk):
    project = get_object_or_404(
        Project.objects.select_related('department', 'manager'), pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'progress':
            if not (request.user.can('projects.update') or request.user.can('projects.manage')):
                raise PermissionDenied('You cannot post progress updates.')
            if 'progress' in request.POST:
                project.progress = max(0, min(100, int(parse_decimal(
                    request.POST.get('progress'), '0'))))
            if 'status' in request.POST:
                project.status = request.POST.get('status', project.status)
            if request.POST.get('spent'):
                project.spent = parse_decimal(request.POST.get('spent'))
            if project.progress >= 100:
                project.status = 'completed'
            project.save()
            log(request.user, 'update', project,
                f'Progress {project.progress}% status {project.status}', request,
                module='projects')
            messages.success(request, 'Project progress updated.')
        elif action == 'milestone':
            if not request.user.can('projects.manage'):
                raise PermissionDenied('You cannot add milestones.')
            title = request.POST.get('title', '').strip()
            if title:
                Milestone.objects.create(
                    project=project, title=title,
                    due_date=parse_date(request.POST.get('due_date')),
                    note=request.POST.get('note', '').strip(),
                )
                messages.success(request, 'Milestone added.')
            else:
                messages.error(request, 'Milestone title is required.')
        elif action == 'milestone_done':
            if not request.user.can('projects.manage'):
                raise PermissionDenied('You cannot update milestones.')
            milestone = get_object_or_404(Milestone, pk=request.POST.get('milestone'),
                                          project=project)
            milestone.status = 'done'
            milestone.completed_on = timezone.localdate()
            milestone.save()
            messages.success(request, 'Milestone marked complete.')
        return redirect('projects_detail', pk=project.pk)

    return render(request, 'projects/detail.html', {
        'project': project,
        'milestones': project.milestones.all(),
        'inspections': project.inspections.select_related('inspector')[:6],
        'statuses': Project.STATUS,
        'page_title': project.code,
    })


@perm_required('projects.view')
def inspections(request):
    rows = Inspection.objects.select_related('project', 'inspector')
    project_id = request.GET.get('project', '')
    if project_id:
        rows = rows.filter(project_id=project_id)
    if request.method == 'POST':
        if not request.user.can('projects.inspect'):
            raise PermissionDenied('You cannot record inspections.')
        project = get_object_or_404(Project, pk=request.POST.get('project'))
        finding = request.POST.get('finding', '').strip()
        if not finding:
            messages.error(request, 'Findings are required.')
        else:
            inspection = Inspection.objects.create(
                project=project,
                date=parse_date(request.POST.get('date')) or timezone.localdate(),
                inspector=request.user,
                location=request.POST.get('location', '').strip(),
                finding=finding,
                rating=request.POST.get('rating', 'pass'),
                follow_up_date=parse_date(request.POST.get('follow_up_date')),
            )
            log(request.user, 'create', inspection,
                f'Inspection recorded for {project.code}', request, module='projects')
            messages.success(request, 'Inspection recorded.')
        return redirect('projects_inspections')
    return render(request, 'projects/inspections.html', {
        'page_obj': paginate(request, rows, 25),
        'projects': Project.objects.exclude(status='completed'),
        'ratings': Inspection.RATING,
        'project_id': project_id,
        'page_title': 'Inspections',
    })
