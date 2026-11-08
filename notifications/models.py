from django.conf import settings
from django.db import models
from django.utils import timezone


class NotificationTemplate(models.Model):
    CHANNELS = [('all', 'In-app + email + SMS'), ('inapp', 'In-app'), ('email', 'Email'),
                ('sms', 'SMS')]
    code = models.SlugField(max_length=60, unique=True)
    name = models.CharField(max_length=120)
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField(
        help_text='Supports {{ user }}, {{ reference }} and other context values.'
    )
    channel = models.CharField(max_length=10, choices=CHANNELS, default='all')
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f'{self.name} ({self.code})'


class Notification(models.Model):
    CHANNELS = [('inapp', 'In-app'), ('email', 'Email'), ('sms', 'SMS')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='notifications')
    channel = models.CharField(max_length=10, choices=CHANNELS, default='inapp')
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField(blank=True)
    url = models.CharField(max_length=255, blank=True)
    template_code = models.CharField(max_length=60, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def is_read(self):
        return self.read_at is not None


class OutboxMessage(models.Model):
    CHANNELS = [('email', 'Email'), ('sms', 'SMS')]
    channel = models.CharField(max_length=10, choices=CHANNELS)
    recipient = models.CharField(max_length=200)
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    template_code = models.CharField(max_length=60, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    simulated = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
