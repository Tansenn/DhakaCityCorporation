from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import perm_required
from notifications.models import Notification, NotificationTemplate, OutboxMessage


@perm_required('notifications.view')
def outbox(request):
    channel = request.GET.get('channel', '')
    q = request.GET.get('q', '').strip()
    rows = OutboxMessage.objects.all()
    if channel:
        rows = rows.filter(channel=channel)
    if q:
        rows = rows.filter(recipient__icontains=q) | rows.filter(body__icontains=q)
    return render(request, 'notifications/outbox.html', {
        'rows': rows[:200], 'channel': channel, 'q': q,
        'templates': NotificationTemplate.objects.all(),
        'page_title': 'Demo outbox',
    })


@perm_required('notifications.manage')
def templates(request):
    rows = NotificationTemplate.objects.all()
    if request.method == 'POST':
        tpl = NotificationTemplate.objects.get(pk=request.POST.get('id'))
        tpl.subject = request.POST.get('subject', tpl.subject)
        tpl.body = request.POST.get('body', tpl.body)
        tpl.save()
        from audit.models import log
        log(request.user, 'settings', tpl, 'Updated notification template', request)
        from django.contrib import messages
        messages.success(request, f'Template "{tpl.name}" updated.')
    return render(request, 'notifications/templates.html', {
        'templates': rows, 'page_title': 'Notification templates',
    })


def my_notifications(request):
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    rows = Notification.objects.filter(user=request.user).order_by('-created_at')[:200]
    if request.method == 'POST' and request.POST.get('mark_all'):
        Notification.objects.filter(user=request.user, read_at__isnull=True).update(
            read_at=timezone.now())
        from django.contrib import messages
        messages.success(request, 'All notifications marked as read.')
    return render(request, 'notifications/list.html', {
        'rows': rows, 'page_title': 'Notifications',
    })
