"""Demo account catalogue shown on the login page and in the role switcher."""
from __future__ import annotations

DEMO_PASSWORD = 'Demo@12345'

CITY_DEMO_ACCOUNTS = [
    ('dscc_citizen', 'Citizen / Applicant'),
    ('dscc_councillor', 'Ward Councillor'),
    ('dscc_officer', 'Department Officer'),
    ('dscc_mayor', 'Mayor / Administrator'),
]


def _demo_rows(pairs, org_code):
    from accounts.models import User

    existing = {
        u.username: u for u in User.objects.filter(
            username__in=[a[0] for a in pairs]
        ).select_related('role')
    }
    out = []
    for username, label in pairs:
        user = existing.get(username)
        out.append({
            'username': username,
            'label': user.role.name if user and user.role else label,
            'name': user.display_name if user else label,
            'role_code': user.role.code if user and user.role else '',
            'org_code': org_code,
        })
    return out


def city_demo_accounts():
    return _demo_rows(CITY_DEMO_ACCOUNTS, 'dscc')


def account_credentials():
    """Credentials used by the seed command and the login helper panel."""
    return [(username, DEMO_PASSWORD, label) for username, label in CITY_DEMO_ACCOUNTS]
