from django.conf import settings
from django.db import models
from django.utils import timezone


class ReportAccessLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             on_delete=models.SET_NULL, related_name='report_access')
    report = models.CharField(max_length=120)
    parameters = models.CharField(max_length=255, blank=True)
    ip = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.report} by {self.user}'
