"""Sidebar navigation, filtered by the signed-in user's permissions."""

NAV = [
    ('Workspace', [
        ('Dashboard', '/app/', None, 'grid-1x2'),
        ('My Tasks', '/app/tasks/', 'workflow.view', 'check2-square'),
    ]),
    ('Approvals', [
        ('Workflow designer', '/app/workflow/', 'workflow.manage', 'diagram-3'),
        ('Authority matrix', '/app/workflow/matrix/', 'workflow.manage', 'shield-check'),
        ('Workflow performance', '/app/mis/workflow/', 'workflow.audit', 'speedometer'),
    ]),
    ('Dakbungalow', [
        ('Booking management', '/app/bookings/', 'bookings.view', 'calendar-check'),
        ('Booking desk queue', '/app/bookings/?queue=desk', 'bookings.review', 'inbox'),
        ('Reception desk', '/app/reception/', 'bookings.reception', 'qr-code-scan'),
        ('Facilities & availability', '/app/facilities/', 'facilities.view', 'building'),
        ('Payments & reconciliation', '/app/payments/', 'payments.view', 'credit-card'),
        ('Refunds', '/app/refunds/', 'payments.refund', 'arrow-counterclockwise'),
    ]),
    ('People', [
        ('Human resources', '/app/hr/', 'hr.view', 'people'),
        ('Employees', '/app/hr/employees/', 'hr.view', 'person-vcard'),
        ('Attendance', '/app/hr/attendance/', 'hr.attendance', 'calendar2-check'),
        ('Leave', '/app/hr/leave/', 'hr.self', 'calendar-x'),
        ('Roster', '/app/hr/roster/', 'hr.roster', 'person-workspace'),
        ('Training & expiry', '/app/hr/training/', 'hr.training', 'mortarboard'),
    ]),
    ('Records', [
        ('Document register', '/app/documents/', 'documents.view', 'journal-text'),
        ('Files', '/app/documents/files/', 'documents.view', 'folder2-open'),
        ('Overdue files', '/app/documents/overdue/', 'documents.view', 'exclamation-circle'),
    ]),
    ('Delivery', [
        ('Projects', '/app/projects/', 'projects.view', 'kanban'),
        ('Inspections', '/app/projects/inspections/', 'projects.view', 'geo-alt'),
        ('Meetings', '/app/meetings/', 'meetings.view', 'calendar-event'),
        ('Action follow-up', '/app/meetings/actions/', 'meetings.view', 'list-check'),
    ]),
    ('Insight', [
        ('Executive dashboard', '/app/mis/', 'mis.view_exec', 'graph-up-arrow'),
        ('Department dashboard', '/app/mis/department/', 'mis.view_dept', 'diagram-2'),
        ('Booking & revenue', '/app/mis/bookings/', 'mis.reports', 'bar-chart'),
        ('Report library', '/app/mis/reports/', 'mis.reports', 'file-earmark-bar-graph'),
    ]),
    ('Governance', [
        ('Audit log', '/app/audit/', 'audit.view', 'shield-lock'),
        ('Users & roles', '/app/users/', 'accounts.view_users', 'person-gear'),
        ('Settings', '/app/settings/', 'accounts.manage_settings', 'sliders'),
        ('Security & backup', '/app/security/', 'accounts.manage_settings', 'lock'),
        ('System health', '/app/health/', 'accounts.manage_settings', 'heart-pulse'),
        ('Demo outbox', '/app/outbox/', 'notifications.view', 'envelope-open'),
    ]),
    ('Support', [
        ('Support tickets', '/app/support/', 'support.view', 'life-preserver'),
        ('45-day plan', '/app/acceptance/', 'support.view', 'calendar3-range'),
        ('Deliverables & UAT', '/app/acceptance/checklists/', 'support.view', 'clipboard-check'),
        ('Change requests', '/app/change-requests/', 'support.view', 'arrow-repeat'),
    ]),
]


def build_nav(user):
    if not user or not user.is_authenticated:
        return []
    is_citizen = user.is_citizen
    groups = []
    for group_label, items in NAV:
        visible = []
        for label, url, perm, icon in items:
            if perm is None:
                if is_citizen:
                    continue
            elif not user.can(perm):
                continue
            visible.append({'label': label, 'url': url, 'icon': icon})
        if visible:
            groups.append({'label': group_label, 'items': visible})
    return groups
