from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Project(models.Model):
    STATUS = [('planning', 'Planning'), ('ongoing', 'Ongoing'),
              ('delayed', 'Delayed'), ('completed', 'Completed'),
              ('cancelled', 'Cancelled')]
    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=200)
    department = models.ForeignKey('hr.Department', null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='projects')
    description = models.TextField(blank=True)
    location = models.CharField(max_length=160, blank=True)
    budget = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    spent = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='planning')
    progress = models.PositiveIntegerField(default=0, help_text='Percent complete')
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                on_delete=models.SET_NULL, related_name='managed_projects')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} {self.name}'

    @property
    def status_label(self):
        return self.get_status_display()

    @property
    def utilisation(self):
        if not self.budget:
            return 0
        return round(float(self.spent) / float(self.budget) * 100, 1)

    @property
    def is_overdue(self):
        return bool(self.end_date and self.end_date < timezone.localdate()
                    and self.status not in ('completed', 'cancelled'))

    @property
    def inspections_count(self):
        return self.inspections.count()


class Milestone(models.Model):
    STATUS = [('pending', 'Pending'), ('in_progress', 'In progress'),
              ('done', 'Completed'), ('slipped', 'Slipped')]
    project = models.ForeignKey(Project, on_delete=models.CASCADE,
                                related_name='milestones')
    title = models.CharField(max_length=160)
    due_date = models.DateField(null=True, blank=True)
    completed_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['due_date', 'title']

    def __str__(self):
        return f'{self.project.code} {self.title}'


class Inspection(models.Model):
    RATING = [('pass', 'Satisfactory'), ('minor', 'Minor observation'),
              ('fail', 'Unsatisfactory')]
    project = models.ForeignKey(Project, on_delete=models.CASCADE,
                                related_name='inspections')
    date = models.DateField(default=timezone.localdate)
    inspector = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                  on_delete=models.SET_NULL, related_name='inspections')
    location = models.CharField(max_length=160, blank=True)
    finding = models.TextField()
    rating = models.CharField(max_length=10, choices=RATING, default='pass')
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f'{self.project.code} {self.date}'
