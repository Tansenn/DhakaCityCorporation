from __future__ import annotations

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import perm_required
from accounts.models import User
from audit.models import log
from core.utils import next_reference, paginate, parse_date, today, validate_upload
from documents.models import DocumentFile, FileMovement
from hr.models import Department


@perm_required('documents.view')
def register(request):
    rows = DocumentFile.objects.select_related('department', 'assigned_to', 'created_by')
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    if q:
        rows = rows.filter(Q(file_no__icontains=q) | Q(subject__icontains=q)
                           | Q(received_from__icontains=q))
    if category:
        rows = rows.filter(category=category)
    if status:
        rows = rows.filter(status=status)
    if not request.user.can('documents.confidential'):
        rows = rows.exclude(confidentiality='confidential')

    if request.method == 'POST':
        if not request.user.can('documents.create'):
            raise PermissionDenied('You cannot create register entries.')
        subject = request.POST.get('subject', '').strip()
        if not subject:
            messages.error(request, 'Subject is required.')
        else:
            attachment = request.FILES.get('attachment')
            try:
                validate_upload(attachment, 'Attachment')
            except ValidationError as exc:
                messages.error(request, exc.messages[0])
                return redirect('documents_register')
            doc = DocumentFile(
                file_no=next_reference('GZP-FL', DocumentFile, 'file_no'),
                subject=subject,
                category=request.POST.get('category', 'general'),
                department=Department.objects.filter(
                    pk=request.POST.get('department')).first(),
                priority=request.POST.get('priority', 'normal'),
                confidentiality=request.POST.get('confidentiality', 'normal'),
                received_from=request.POST.get('received_from', '').strip(),
                assigned_to=User.objects.filter(pk=request.POST.get('assigned_to')).first(),
                created_by=request.user,
                due_date=parse_date(request.POST.get('due_date')),
                attachment=attachment,
                notes=request.POST.get('notes', '').strip(),
            )
            doc.save()
            FileMovement.objects.create(
                file=doc, action='register', from_user=request.user,
                to_user=doc.assigned_to, note='File registered',
            )
            log(request.user, 'create', doc, f'File registered: {doc.file_no}', request,
                module='documents')
            messages.success(request, f'File {doc.file_no} registered.')
            return redirect('documents_register')

    counts = {
        'open': DocumentFile.objects.filter(status='open').count(),
        'in_progress': DocumentFile.objects.filter(status='in_progress').count(),
        'overdue': sum(1 for d in DocumentFile.objects.all() if d.is_overdue),
        'closed': DocumentFile.objects.filter(status__in=('closed', 'archived')).count(),
    }
    return render(request, 'documents/register.html', {
        'page_obj': paginate(request, rows, 25),
        'counts': counts,
        'categories': DocumentFile.CATEGORIES,
        'statuses': DocumentFile.STATUS,
        'priorities': DocumentFile.PRIORITY,
        'departments': Department.objects.all(),
        'users': User.objects.filter(is_active=True).select_related('role'),
        'q': q, 'category': category, 'status': status,
        'page_title': 'Document register',
    })


@perm_required('documents.view')
def file_detail(request, pk):
    doc = get_object_or_404(
        DocumentFile.objects.select_related('department', 'assigned_to', 'created_by'), pk=pk)
    if doc.confidentiality == 'confidential' and not (
            request.user.can('documents.confidential')
            or request.user.pk in (doc.created_by_id, doc.assigned_to_id)):
        raise PermissionDenied('This file is confidential.')

    if request.method == 'POST':
        if not request.user.can('documents.move'):
            raise PermissionDenied('You cannot move files.')
        action = request.POST.get('action', 'note')
        note = request.POST.get('note', '').strip()
        to_user = User.objects.filter(pk=request.POST.get('to_user')).first()
        if action == 'forward':
            doc.assigned_to = to_user
            doc.status = 'in_progress'
        elif action == 'receive':
            doc.assigned_to = request.user
            doc.status = 'in_progress'
        elif action == 'close':
            doc.status = 'closed'
        elif action == 'return':
            doc.status = 'open'
            doc.assigned_to = doc.created_by
        FileMovement.objects.create(
            file=doc, action=action, from_user=request.user,
            to_user=to_user if action == 'forward' else doc.assigned_to,
            note=note or action.title(),
        )
        doc.save(update_fields=['assigned_to', 'status', 'updated_at'])
        log(request.user, 'update', doc, f'File {doc.file_no}: {action} {note}'.strip(),
            request, module='documents')
        messages.success(request, 'File movement recorded.')
        return redirect('documents_file', pk=doc.pk)

    return render(request, 'documents/file_detail.html', {
        'doc': doc,
        'movements': doc.movements.select_related('from_user', 'to_user'),
        'users': User.objects.filter(is_active=True).select_related('role'),
        'actions': FileMovement.ACTIONS,
        'page_title': doc.file_no,
    })


@perm_required('documents.view')
def files(request):
    rows = DocumentFile.objects.exclude(attachment='').select_related('department')
    if not request.user.can('documents.confidential'):
        rows = rows.exclude(confidentiality='confidential')
    q = request.GET.get('q', '').strip()
    if q:
        rows = rows.filter(Q(subject__icontains=q) | Q(file_no__icontains=q))
    return render(request, 'documents/files.html', {
        'rows': rows, 'q': q, 'page_title': 'Files',
    })


@perm_required('documents.view')
def overdue(request):
    rows = [d for d in DocumentFile.objects.select_related('department', 'assigned_to')
            if d.is_overdue]
    if not request.user.can('documents.confidential'):
        rows = [d for d in rows if d.confidentiality != 'confidential']
    return render(request, 'documents/overdue.html', {
        'rows': rows, 'today': today(), 'page_title': 'Overdue files',
    })


@perm_required('documents.audit')
def access_log(request):
    rows = FileMovement.objects.select_related('file', 'from_user', 'to_user')[:400]
    return render(request, 'documents/access_log.html', {
        'rows': rows, 'page_title': 'Document access log',
    })
