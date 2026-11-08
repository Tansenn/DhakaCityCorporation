from django.conf import settings
from django.db import models
from django.utils import timezone


class DocumentFile(models.Model):
    CATEGORIES = [
        ('general', 'General correspondence'),
        ('procurement', 'Procurement'),
        ('legal', 'Legal / statutory'),
        ('hr', 'Human resources'),
        ('project', 'Project file'),
        ('finance', 'Finance'),
        ('other', 'Other'),
    ]
    STATUS = [('open', 'Open'), ('in_progress', 'In progress'),
              ('closed', 'Closed'), ('archived', 'Archived')]
    PRIORITY = [('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')]
    CONFIDENTIALITY = [('normal', 'Normal'), ('confidential', 'Confidential')]

    file_no = models.CharField(max_length=40, unique=True)
    subject = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORIES, default='general')
    department = models.ForeignKey('hr.Department', null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='document_files')
    status = models.CharField(max_length=20, choices=STATUS, default='open')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='normal')
    confidentiality = models.CharField(max_length=20, choices=CONFIDENTIALITY,
                                       default='normal')
    received_from = models.CharField(max_length=160, blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='assigned_files')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='created_files')
    due_date = models.DateField(null=True, blank=True)
    attachment = models.FileField(upload_to='documents/', blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.file_no} {self.subject}'

    @property
    def is_overdue(self):
        return bool(self.due_date and self.due_date < timezone.localdate()
                    and self.status not in ('closed', 'archived'))

    @property
    def status_label(self):
        return self.get_status_display()

    @property
    def workflow_instance(self):
        from workflow.models import WorkflowInstance

        return WorkflowInstance.objects.filter(
            object_type='documents.DocumentFile', object_id=self.pk
        ).order_by('-created_at').first()

    def on_workflow_decision(self, decision, instance):
        if instance.status == 'approved':
            self.status = 'closed'
        elif decision == 'reject':
            self.status = 'open'
        else:
            self.status = 'in_progress'
        self.save(update_fields=['status', 'updated_at'])


class FileMovement(models.Model):
    ACTIONS = [('register', 'Registered'), ('forward', 'Forwarded'),
               ('receive', 'Received'), ('return', 'Returned'),
               ('close', 'Closed'), ('note', 'Note added')]
    file = models.ForeignKey(DocumentFile, on_delete=models.CASCADE,
                             related_name='movements')
    action = models.CharField(max_length=20, choices=ACTIONS, default='note')
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                  on_delete=models.SET_NULL, related_name='+')
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                on_delete=models.SET_NULL, related_name='+')
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.file.file_no} {self.action}'
