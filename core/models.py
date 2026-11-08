from django.conf import settings
from django.db import models
from django.utils import timezone


class AppSetting(models.Model):
    """Editable configuration / master-data values (sample values, admin editable)."""

    key = models.CharField(max_length=120, unique=True)
    value = models.TextField(blank=True)
    label = models.CharField(max_length=160, blank=True)
    group = models.CharField(max_length=60, default='General')
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )

    class Meta:
        ordering = ['group', 'key']

    def __str__(self):
        return f'{self.key}={self.value}'


class SettingHistory(models.Model):
    key = models.CharField(max_length=120)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    changed_at = models.DateTimeField(default=timezone.now)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-changed_at']


class BackupRecord(models.Model):
    filename = models.CharField(max_length=255)
    size_bytes = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-created_at']


class HealthEvent(models.Model):
    KIND = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    kind = models.CharField(max_length=10, choices=KIND, default='info')
    message = models.CharField(max_length=255)
    path = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']


def get_setting(key, default=''):
    from core.models import AppSetting

    try:
        return AppSetting.objects.get(key=key).value
    except AppSetting.DoesNotExist:
        return default


def get_int(key, default=0):
    try:
        return int(float(get_setting(key, default)))
    except (TypeError, ValueError):
        return default


def get_decimal(key, default=0):
    from decimal import Decimal, InvalidOperation

    try:
        return Decimal(str(get_setting(key, default)))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(str(default))


def get_bool(key, default=False):
    value = str(get_setting(key, '1' if default else '0')).lower()
    return value in ('1', 'true', 'yes', 'on')


def set_setting(key, value, user=None, note=''):
    from core.models import AppSetting, SettingHistory

    obj, created = AppSetting.objects.get_or_create(key=key)
    old = '' if created else obj.value
    obj.value = str(value)
    obj.updated_by = user if user and user.is_authenticated else None
    obj.save()
    if old != str(value):
        SettingHistory.objects.create(
            key=key, old_value=old, new_value=str(value),
            changed_by=obj.updated_by, note=note,
        )
    return obj
