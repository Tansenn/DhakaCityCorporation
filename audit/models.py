from django.conf import settings
from django.db import models
from django.utils import timezone


class AuditEntry(models.Model):
    ACTIONS = [
        ('login', 'Login'), ('logout', 'Logout'), ('create', 'Create'),
        ('update', 'Update'), ('delete', 'Delete'), ('upload', 'Upload'),
        ('move', 'File movement'), ('decision', 'Decision'),
        ('payment', 'Payment'), ('settings', 'Settings change'),
        ('export', 'Export'), ('backup', 'Backup'), ('verify', 'Verification'),
    ]
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              on_delete=models.SET_NULL, related_name='audit_entries')
    actor_label = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=20, choices=ACTIONS)
    module = models.CharField(max_length=40, blank=True)
    model = models.CharField(max_length=80, blank=True)
    object_id = models.CharField(max_length=40, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    changes = models.TextField(blank=True)
    ip = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.actor_label} {self.action} {self.object_repr}'


def log(actor, action, obj=None, changes='', request=None, module=''):
    from core.utils import get_client_ip

    if obj is not None and not module:
        module = obj._meta.app_label
    return AuditEntry.objects.create(
        actor=actor if getattr(actor, 'is_authenticated', False) else None,
        actor_label=(actor.display_name if getattr(actor, 'is_authenticated', False)
                     else 'system'),
        action=action,
        module=module or '',
        model=obj._meta.label if obj is not None else '',
        object_id=str(getattr(obj, 'pk', '') or ''),
        object_repr=str(obj)[:255] if obj is not None else '',
        changes=str(changes)[:4000],
        ip=get_client_ip(request) if request else '',
    )
