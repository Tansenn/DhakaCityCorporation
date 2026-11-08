from __future__ import annotations

from django import template
from django.utils import formats, timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from core import i18n
from core.utils import money as money_fmt

register = template.Library()


@register.simple_tag(takes_context=True)
def t(context, text):
    return i18n.translate(text, context.get('lang', 'en'))


@register.filter
def tr(value, lang):
    return i18n.translate(str(value), lang)


@register.filter
def money(value):
    return money_fmt(value)


@register.filter
def chip(value):
    """Status chip class for a status code or label."""
    key = str(value or '').lower().replace(' ', '_').replace('/', '_')
    mapping = {
        'submitted': 'info', 'under_review': 'warning', 'clarification': 'amber',
        'clarification_required': 'amber', 'recommended': 'primary',
        'approved': 'success', 'rejected': 'danger', 'awaiting_payment': 'amber',
        'paid': 'teal', 'paid_/_confirmed': 'teal', 'cancelled': 'muted',
        'completed': 'success', 'pending': 'warning', 'overdue': 'danger',
        'returned': 'amber', 'in_progress': 'info', 'open': 'warning',
        'resolved': 'success', 'closed': 'muted', 'active': 'success',
        'inactive': 'muted', 'archived': 'muted', 'success': 'success',
        'failed': 'danger', 'duplicate': 'amber', 'refunded': 'teal',
        'requested': 'warning', 'processed': 'success', 'matched': 'success',
        'mismatched': 'danger', 'paid_confirmed': 'teal', 'escalated': 'danger',
        'passed': 'success', 'pass': 'success', 'fail': 'danger',
        'draft': 'muted', 'running': 'info', 'verified': 'success',
        'present': 'success', 'absent': 'danger', 'late': 'amber',
        'leave': 'info', 'planning': 'info', 'ongoing': 'primary',
        'delayed': 'danger', 'scheduled': 'info', 'held': 'success',
        'open_ticket': 'warning', 'acknowledged': 'info',
        'paused': 'muted', 'unpaid': 'warning', 'issued': 'info',
    }
    return mapping.get(key, 'muted')


@register.filter
def device_label(value, lang):
    return i18n.status_bn(str(value)) if lang == 'bn' else value


@register.filter
def dt(value, fmt='d M Y, H:i'):
    if not value:
        return '-'
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return formats.date_format(value, fmt)


@register.filter
def d(value, fmt='d M Y'):
    if not value:
        return '-'
    return formats.date_format(value, fmt)


@register.filter
def can(code, user):
    return bool(user and user.is_authenticated and user.can(code))


@register.filter
def has_role(user, role_code):
    return bool(user and user.is_authenticated and user.role and user.role.code == role_code)


@register.filter
def initials(value):
    parts = [p for p in str(value or '').split() if p]
    return ''.join(p[0].upper() for p in parts[:2]) or '?'


@register.filter
def get_item(mapping, key):
    if mapping is None:
        return None
    try:
        return mapping.get(key)
    except AttributeError:
        return None


@register.filter
def percent(part, whole):
    try:
        part = float(part or 0)
        whole = float(whole or 0)
        if not whole:
            return 0
        return round(part / whole * 100, 1)
    except (TypeError, ValueError):
        return 0


@register.simple_tag
def query_replace(request, **kwargs):
    params = request.GET.copy()
    for key, value in kwargs.items():
        if value in (None, ''):
            params.pop(key, None)
        else:
            params[key] = value
    return params.urlencode()


@register.simple_tag
def nav_active(request, prefix):
    path = request.path
    if prefix == '/app/':
        return 'active' if path == '/app/' else ''
    return 'active' if path.startswith(prefix) else ''


@register.filter
def bool_icon(value):
    if value:
        return format_html('<i class="bi bi-check-circle-fill text-success"></i>')
    return format_html('<i class="bi bi-dash-circle text-muted"></i>')


@register.filter
def truncate_words_custom(value, count=18):
    words = str(value or '').split()
    if len(words) <= count:
        return value
    return mark_safe(' '.join(words[:count]) + '&hellip;')
