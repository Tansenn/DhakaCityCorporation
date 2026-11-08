from django.conf import settings
from django.db import models
from django.utils import timezone


class Meeting(models.Model):
    STATUS = [('scheduled', 'Scheduled'), ('held', 'Held'), ('cancelled', 'Cancelled')]
    title = models.CharField(max_length=200)
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    venue = models.CharField(max_length=160, blank=True)
    agenda = models.TextField(blank=True)
    minutes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='scheduled')
    chair = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              on_delete=models.SET_NULL, related_name='chaired_meetings')
    secretary = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                  on_delete=models.SET_NULL, related_name='minuted_meetings')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f'{self.title} ({self.date})'

    @property
    def status_label(self):
        return self.get_status_display()

    @property
    def open_actions(self):
        return self.actions.exclude(status='done').count()


class Attendee(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='attendees')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             on_delete=models.SET_NULL, related_name='meeting_attendance')
    name = models.CharField(max_length=160)
    role = models.CharField(max_length=120, blank=True)
    present = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.meeting.title}: {self.name}'


class ActionItem(models.Model):
    STATUS = [('open', 'Open'), ('in_progress', 'In progress'), ('done', 'Completed'),
              ('cancelled', 'Cancelled')]
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='actions')
    description = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              on_delete=models.SET_NULL, related_name='meeting_actions')
    owner_label = models.CharField(max_length=120, blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='open')
    completed_at = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['due_date', 'id']

    def __str__(self):
        return self.description

    @property
    def is_overdue(self):
        return bool(self.due_date and self.due_date < timezone.localdate()
                    and self.status not in ('done', 'cancelled'))
