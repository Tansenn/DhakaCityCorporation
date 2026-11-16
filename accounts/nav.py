"""Sidebar navigation for the city corporation portal."""

CITY_NAV = [
    ('City dashboard', '/app/city/', 'city.view', 'speedometer2'),
    ('City services', '/dscc/', 'city.view', 'building-gear'),
    ('Application forms', '/dscc/forms/', 'city.view', 'file-earmark-text'),
    ('Offices and departments', '/dscc/offices/', 'city.view', 'building'),
    ('Acts, rules and gazettes', '/dscc/acts/', 'city.view', 'journal-bookmark'),
    ('My city applications', '/dscc/applications/', 'city.view', 'folder2-open'),
    ('Verification queue', '/app/city/queue/', 'city.verify', 'inbox'),
    ('Zones and wards', '/app/city/setup/', 'city.manage', 'geo-alt'),
]

ADMIN_NAV = [
    ('Activity log', '/app/audit/', 'audit.view', 'shield-lock'),
    ('Users & roles', '/app/users/', 'accounts.view_users', 'person-gear'),
    ('Settings', '/app/settings/', 'accounts.manage_settings', 'sliders'),
    ('Security & backup', '/app/security/', 'accounts.manage_settings', 'lock'),
    ('System status', '/app/health/', 'accounts.manage_settings', 'heart-pulse'),
    ('Mail outbox', '/app/outbox/', 'notifications.view', 'envelope-open'),
]


def _visible(user, items):
    return [
        {'label': label, 'url': url, 'icon': icon}
        for label, url, perm, icon in items
        if user.can(perm)
    ]


def build_nav(user, org=None):
    if not user or not user.is_authenticated:
        return []
    groups = []
    city = _visible(user, CITY_NAV)
    if city:
        groups.append({'label': 'City corporation', 'items': city})
    admin = _visible(user, ADMIN_NAV)
    if admin:
        groups.append({'label': 'Administration', 'items': admin})
    return groups
