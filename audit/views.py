from django.db.models import Q
from django.shortcuts import render

from accounts.decorators import perm_required
from audit.models import AuditEntry
from core.utils import csv_response, parse_date


def filtered_entries(request):
    rows = AuditEntry.objects.select_related('actor').all()
    q = request.GET.get('q', '').strip()
    action = request.GET.get('action', '')
    module = request.GET.get('module', '')
    date_from = parse_date(request.GET.get('from'))
    date_to = parse_date(request.GET.get('to'))
    if q:
        rows = rows.filter(
            Q(actor_label__icontains=q) | Q(object_repr__icontains=q)
            | Q(changes__icontains=q) | Q(ip__icontains=q)
        )
    if action:
        rows = rows.filter(action=action)
    if module:
        rows = rows.filter(module=module)
    if date_from:
        rows = rows.filter(created_at__date__gte=date_from)
    if date_to:
        rows = rows.filter(created_at__date__lte=date_to)
    return rows



@perm_required('audit.view')
def audit_list(request):
    rows = filtered_entries(request)
    modules = AuditEntry.objects.values_list('module', flat=True).distinct()
    return render(request, 'audit/list.html', {
        'rows': rows[:500],
        'total': rows.count(),
        'actions': AuditEntry.ACTIONS,
        'modules': sorted({m for m in modules if m}),
        'q': request.GET.get('q', ''),
        'selected_action': request.GET.get('action', ''),
        'selected_module': request.GET.get('module', ''),
        'page_title': 'Audit log',
    })


@perm_required('audit.export')
def audit_export(request):
    rows = filtered_entries(request)[:10000]
    from audit.models import log
    log(request.user, 'export', changes='Audit log CSV export', request=request,
        module='audit')
    return csv_response('audit-log.csv',
                        ['When', 'Actor', 'Action', 'Module', 'Object', 'Changes', 'IP'],
                        [(r.created_at.strftime('%Y-%m-%d %H:%M:%S'), r.actor_label,
                          r.action, r.module, r.object_repr, r.changes, r.ip)
                         for r in rows])
