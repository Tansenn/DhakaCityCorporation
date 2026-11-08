"""Notification fan-out. Nothing leaves the machine: email/SMS land in the
demo outbox and are labelled simulated."""
from __future__ import annotations

from django.template import Context, Template

from notifications.models import Notification, NotificationTemplate, OutboxMessage


def _render(text, user, context):
    data = {'user': user.display_name if user else 'Applicant', 'username': user.username if user else ''}
    data.update({k: v for k, v in (context or {}).items() if v is not None})
    try:
        return Template(text or '').render(Context(data))
    except Exception:
        return text or ''


def send(user, template_code, context=None, url='', channels=None):
    """Create in-app notifications and simulated email/SMS outbox entries."""
    if user is None:
        return None
    template = NotificationTemplate.objects.filter(code=template_code).first()
    if template:
        subject = _render(template.subject, user, context) or template.name
        body = _render(template.body, user, context)
    else:
        subject = (context or {}).get('subject', 'Notification')
        body = (context or {}).get('body', '')

    if channels is None:
        channels = ['inapp', 'email', 'sms']

    note = None
    if 'inapp' in channels:
        note = Notification.objects.create(
            user=user, channel='inapp', subject=subject, body=body,
            url=url[:255], template_code=template_code,
        )
    if 'email' in channels and user.email:
        OutboxMessage.objects.create(
            channel='email', recipient=user.email, subject=subject, body=body,
            template_code=template_code,
        )
    if 'sms' in channels and user.phone:
        OutboxMessage.objects.create(
            channel='sms', recipient=user.phone, subject=subject[:160],
            body=body, template_code=template_code,
        )
    return note


def send_raw(user, subject, body, url=''):
    if user is None:
        return None
    Notification.objects.create(user=user, subject=subject, body=body, url=url)
    if user.email:
        OutboxMessage.objects.create(channel='email', recipient=user.email,
                                     subject=subject, body=body)
    if user.phone:
        OutboxMessage.objects.create(channel='sms', recipient=user.phone,
                                     subject=subject, body=body)
    return None
