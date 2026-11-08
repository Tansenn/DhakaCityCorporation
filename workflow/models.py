from django.conf import settings
from django.db import models
from django.utils import timezone

DECISIONS = [
    ('forward', 'Review and forward'),
    ('recommend', 'Recommend'),
    ('approve', 'Approve'),
    ('reject', 'Reject'),
    ('correct', 'Request correction'),
    ('return', 'Return for correction'),
]
DECISION_CODES = [d[0] for d in DECISIONS]


class WorkflowTemplate(models.Model):
    CATEGORIES = [
        ('booking', 'Booking application'),
        ('leave', 'Leave application'),
        ('file', 'Document file'),
        ('project', 'Project action'),
    ]
    code = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return self.name


class WorkflowStep(models.Model):
    template = models.ForeignKey(WorkflowTemplate, on_delete=models.CASCADE,
                                 related_name='steps')
    order = models.PositiveIntegerField(default=1)
    name = models.CharField(max_length=120)
    role = models.ForeignKey('accounts.Role', on_delete=models.PROTECT,
                             related_name='workflow_steps')
    allowed_decisions = models.JSONField(
        default=list,
        help_text='List of decision codes allowed at this step.',
    )
    condition = models.JSONField(
        null=True, blank=True,
        help_text='Optional JSON condition evaluated against the request payload. '
                  'e.g. {"unit_kind": ["suite", "hall"]} or '
                  '{"any": [{"min_nights": 4}, {"applicant_category": ["organization"]}]}',
    )
    sla_hours = models.PositiveIntegerField(default=24)
    is_final = models.BooleanField(default=False)

    class Meta:
        ordering = ['template', 'order']
        unique_together = [('template', 'order')]

    def __str__(self):
        return f'{self.template.code} #{self.order} {self.name}'

    @property
    def decision_labels(self):
        mapping = dict(DECISIONS)
        return [(code, mapping.get(code, code)) for code in self.allowed_decisions]


class WorkflowInstance(models.Model):
    STATUS = [
        ('running', 'In progress'),
        ('returned', 'Returned for correction'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    template = models.ForeignKey(WorkflowTemplate, on_delete=models.PROTECT,
                                 related_name='instances')
    object_type = models.CharField(max_length=80)
    object_id = models.PositiveIntegerField()
    tracking_id = models.CharField(max_length=60, unique=True)
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                  on_delete=models.SET_NULL, related_name='workflow_requests')
    status = models.CharField(max_length=20, choices=STATUS, default='running')
    current_step = models.ForeignKey(WorkflowStep, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='+')
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.tracking_id

    @property
    def object(self):
        from django.apps import apps

        try:
            model = apps.get_model(self.object_type)
            return model.objects.filter(pk=self.object_id).first()
        except Exception:
            return None

    @property
    def object_url(self):
        return self.payload.get('url', '')

    @property
    def subject(self):
        return self.payload.get('subject', self.tracking_id)

    @property
    def amount(self):
        try:
            return float(self.payload.get('amount') or 0)
        except (TypeError, ValueError):
            return 0


class WorkflowTask(models.Model):
    STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
    ]
    PRIORITY = [('low', 'Low'), ('normal', 'Normal'), ('high', 'High'),
                ('urgent', 'Urgent')]
    instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE,
                                 related_name='tasks')
    step = models.ForeignKey(WorkflowStep, on_delete=models.PROTECT, related_name='tasks')
    role = models.ForeignKey('accounts.Role', on_delete=models.PROTECT, related_name='tasks')
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name='tasks')
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='normal')
    due_at = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    escalated_at = models.DateTimeField(null=True, blank=True)
    escalated_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='escalations')

    class Meta:
        ordering = ['due_at', '-created_at']

    def __str__(self):
        return f'{self.instance.tracking_id} - {self.step.name}'

    @property
    def is_overdue(self):
        return self.status == 'pending' and self.due_at < timezone.now()

    @property
    def queue_label(self):
        if self.status == 'pending' and self.is_overdue:
            return 'Overdue'
        return self.get_status_display()


class StepRecord(models.Model):
    instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE,
                                 related_name='records')
    step = models.ForeignKey(WorkflowStep, null=True, blank=True,
                             on_delete=models.SET_NULL, related_name='+')
    task = models.ForeignKey(WorkflowTask, null=True, blank=True,
                             on_delete=models.SET_NULL, related_name='+')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              on_delete=models.SET_NULL, related_name='workflow_records')
    actor_role = models.CharField(max_length=80, blank=True)
    decision = models.CharField(max_length=20, choices=DECISIONS + [('submit', 'Submitted')],
                                default='submit')
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.instance.tracking_id} {self.decision}'


class AuthorityMatrix(models.Model):
    CATEGORIES = WorkflowTemplate.CATEGORIES
    role = models.ForeignKey('accounts.Role', on_delete=models.CASCADE,
                             related_name='authorities')
    category = models.CharField(max_length=20, choices=CATEGORIES)
    can_approve = models.BooleanField(default=False)
    max_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text='Leave blank for unlimited authority within this category.',
    )
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['category', 'role__sort_order']
        unique_together = [('role', 'category')]

    def __str__(self):
        return f'{self.role.code}:{self.category}'
