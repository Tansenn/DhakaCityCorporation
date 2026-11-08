from django.conf import settings
from django.db import models
from django.utils import timezone


class Ticket(models.Model):
    PRIORITY = [('critical', 'Critical'), ('high', 'High'),
                ('medium', 'Medium'), ('low', 'Low')]
    STATUS = [('open', 'Open'), ('acknowledged', 'Acknowledged'),
              ('in_progress', 'In progress'), ('resolved', 'Resolved'),
              ('closed', 'Closed')]
    CATEGORIES = [('incident', 'Incident / fault'), ('request', 'Service request'),
                  ('access', 'Access / account'), ('data', 'Data correction'),
                  ('other', 'Other')]
    number = models.CharField(max_length=30, unique=True)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORIES, default='incident')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='medium')
    status = models.CharField(max_length=20, choices=STATUS, default='open')
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                  on_delete=models.SET_NULL, related_name='tickets')
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name='assigned_tickets')
    response_due_at = models.DateTimeField(null=True, blank=True)
    resolution = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.number} {self.subject}'

    @property
    def status_label(self):
        return self.get_status_display()

    @property
    def is_overdue(self):
        return bool(self.response_due_at and not self.resolved_at
                    and self.response_due_at < timezone.now())


class PlanPhase(models.Model):
    STATUS = [('done', 'Completed'), ('active', 'In progress'), ('planned', 'Planned')]
    phase = models.CharField(max_length=120)
    window = models.CharField(max_length=80, help_text='Day range, e.g. Day 1-5')
    deliverable = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS, default='planned')
    owner = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.phase


class ChecklistItem(models.Model):
    KINDS = [('deliverable', 'Deliverable'), ('uat', 'UAT test')]
    STATUS = [('pending', 'Pending'), ('passed', 'Passed'), ('failed', 'Failed'),
              ('waived', 'Waived')]
    kind = models.CharField(max_length=20, choices=KINDS, default='deliverable')
    area = models.CharField(max_length=120)
    item = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    note = models.CharField(max_length=255, blank=True)
    checked_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='+')
    checked_at = models.DateTimeField(null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ['kind', 'sort_order']

    def __str__(self):
        return f'{self.area}: {self.item}'


class ChangeRequest(models.Model):
    STATUS = [('proposed', 'Proposed'), ('approved', 'Approved'),
              ('rejected', 'Rejected'), ('implemented', 'Implemented')]
    IMPACT = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]
    reference = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    impact = models.CharField(max_length=10, choices=IMPACT, default='medium')
    status = models.CharField(max_length=20, choices=STATUS, default='proposed')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='change_requests')
    decision_note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.reference} {self.title}'
