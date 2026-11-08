"""Demo account catalogue shown on the login page and in the role switcher."""
from __future__ import annotations

DEMO_PASSWORD = 'Demo@12345'

DEMO_ACCOUNTS = [
    ('citizen1', 'Citizen / Applicant'),
    ('citizen2', 'Citizen / Applicant'),
    ('bookingdesk', 'Booking Desk'),
    ('engineer', 'Technical Reviewer'),
    ('eo', 'Executive Officer'),
    ('ceo', 'CEO / Chairman'),
    ('reception', 'Reception / Facility Operator'),
    ('finance', 'Finance / Accounts'),
    ('hradmin', 'HR Admin'),
    ('supervisor', 'Supervisor'),
    ('employee1', 'Employee'),
    ('depthead', 'Department Head'),
    ('registry', 'Registry / Section Officer'),
    ('projectofficer', 'Project Officer'),
    ('inspector', 'Inspector'),
    ('secretary', 'Meeting Secretary'),
    ('management', 'Management / Auditor (read-only)'),
    ('admin', 'System Administrator'),
]


def demo_accounts():
    from accounts.models import User

    existing = {
        u.username: u for u in User.objects.filter(
            username__in=[a[0] for a in DEMO_ACCOUNTS]
        ).select_related('role')
    }
    out = []
    for username, label in DEMO_ACCOUNTS:
        user = existing.get(username)
        out.append({
            'username': username,
            'label': user.role.name if user and user.role else label,
            'name': user.display_name if user else label,
            'role_code': user.role.code if user and user.role else '',
        })
    return out


def account_credentials():
    """Credentials used by the seed command and the login helper panel."""
    return [(username, DEMO_PASSWORD, label) for username, label in DEMO_ACCOUNTS]
