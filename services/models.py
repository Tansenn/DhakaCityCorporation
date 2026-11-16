import os
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone


class Service(models.Model):
    """A public-facing service shown in a service directory."""

    organization = models.ForeignKey(
        'organizations.Organization', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='services',
    )
    code = models.SlugField(max_length=60)
    name = models.CharField(max_length=90)
    name_bn = models.CharField(max_length=140, blank=True)
    icon = models.CharField(max_length=40, default='grid')
    department = models.CharField(max_length=90, blank=True)
    summary = models.TextField(blank=True)
    fee = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    processing_days = models.PositiveSmallIntegerField(default=7)
    requirements = models.TextField(blank=True, help_text='One requirement per line.')
    sort = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort', 'name']
        unique_together = [('organization', 'code')]

    def __str__(self):
        return self.name

    def requirement_list(self):
        return [line.strip() for line in self.requirements.splitlines() if line.strip()]

    @property
    def department_short(self):
        overrides = {
            "Office of the Hon'ble Administrator": "Administrator's Office",
            'Social Welfare and Slum Development Department': 'Social Welfare',
        }
        if self.department in overrides:
            return overrides[self.department]
        return (self.department or '').removesuffix(' Department')


class ServiceForm(models.Model):
    CATEGORIES = [
        ('parishad', 'Parishad service'),
        ('city', 'City corporation'),
        ('office', 'Office and HR'),
    ]
    TYPES = [
        ('application', 'Application'),
        ('renewal', 'Renewal'),
        ('licence', 'Licence'),
        ('information', 'Information'),
        ('employment', 'Employment'),
    ]

    service = models.ForeignKey(Service, null=True, blank=True, on_delete=models.SET_NULL,
                                related_name='forms')
    organization = models.ForeignKey(
        'organizations.Organization', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='forms',
    )
    sl = models.PositiveSmallIntegerField(default=0)
    title = models.CharField(max_length=200)
    title_bn = models.CharField(max_length=220, blank=True)
    form_no = models.CharField(max_length=30, blank=True)
    form_type = models.CharField(max_length=20, choices=TYPES, default='application')
    category = models.CharField(max_length=20, choices=CATEGORIES, default='parishad')
    fields = models.TextField(blank=True, help_text='One field label per line.')
    has_sample = models.BooleanField(default=False)
    sort = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sort', 'sl']

    def __str__(self):
        return f'{self.sl}. {self.title}'

    def field_list(self):
        return [line.strip() for line in self.fields.splitlines()
                if line.strip() and not line.strip().startswith('#')]

    def field_specs(self):
        """Typed field rows for the web form and the PDF.

        One line per field. `# Title` starts a section. A field is
        `Label`, or `Label|type`, or `Label|type|Option A;Option B`.
        """
        allowed = {'text', 'textarea', 'number', 'date', 'select', 'radio',
                   'nid', 'mobile', 'email', 'attach'}
        specs, index = [], 0
        for raw in self.fields.splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.startswith('#'):
                title = line.lstrip('#').strip()
                if title:
                    specs.append({'kind': 'section', 'label': title})
                continue
            parts = [part.strip() for part in line.split('|')]
            label = parts[0]
            kind = parts[1].lower() if len(parts) > 1 else 'text'
            if kind not in allowed:
                kind = 'text'
            options = []
            if kind in ('select', 'radio') and len(parts) > 2:
                options = [opt.strip() for opt in parts[2].split(';') if opt.strip()]
            lowered = label.lower()
            optional = kind == 'attach' or 'optional' in lowered or 'if any' in lowered
            # Do not print the optional tag twice when the label already says it.
            show_optional = optional and 'optional' not in lowered and 'if any' not in lowered
            index += 1
            specs.append({
                'kind': 'field',
                'index': index,
                'key': f'f{index}',
                'label': label,
                'type': kind,
                'options': options,
                'optional': optional,
                'show_optional': show_optional,
                'value': '',
            })
        return specs

    @property
    def download_name(self):
        return f'gzp-form-{self.sl:02d}.pdf'


class VerificationRoute(models.Model):
    """Ordered verification stages for online applications of one organisation.

    A service-specific route overrides the organisation default, so routes are
    configured as data instead of being hard-coded in the views.
    """

    organization = models.ForeignKey(
        'organizations.Organization', on_delete=models.CASCADE,
        related_name='verification_routes',
    )
    service = models.ForeignKey(Service, null=True, blank=True, on_delete=models.CASCADE,
                                related_name='routes')
    order = models.PositiveSmallIntegerField(default=1)
    role = models.ForeignKey('accounts.Role', on_delete=models.PROTECT, related_name='city_routes')
    label = models.CharField(max_length=80)
    is_final = models.BooleanField(default=False)

    class Meta:
        ordering = ['organization', 'service', 'order']

    def __str__(self):
        return f'{self.organization.code} #{self.order} {self.label}'


class ServiceApplication(models.Model):
    STATUSES = [
        ('submitted', 'Submitted'),
        ('in_review', 'Under verification'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('returned', 'Returned for correction'),
    ]

    reference = models.CharField(max_length=40, unique=True)
    organization = models.ForeignKey(
        'organizations.Organization', on_delete=models.CASCADE,
        related_name='applications',
    )
    form = models.ForeignKey(ServiceForm, on_delete=models.PROTECT,
                             related_name='applications')
    service = models.ForeignKey(Service, null=True, blank=True, on_delete=models.SET_NULL,
                                related_name='applications')
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='service_applications')
    ward = models.ForeignKey('organizations.Ward', null=True, blank=True,
                             on_delete=models.SET_NULL, related_name='applications')
    data = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default='submitted')
    current_order = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.reference

    @property
    def sla_pct(self):
        """Share of the promised processing window still left (100 fresh, 0 past due)."""
        if not self.service or not self.service.processing_days:
            return 100
        window = self.service.processing_days * 86400
        elapsed = (timezone.now() - self.created_at).total_seconds()
        return max(0, min(100, int((1 - elapsed / window) * 100)))

    def stages(self):
        specific = list(VerificationRoute.objects.filter(
            organization=self.organization, service=self.service).order_by('order'))
        if specific:
            return specific
        return list(VerificationRoute.objects.filter(
            organization=self.organization, service__isnull=True).order_by('order'))

    @property
    def current_stage(self):
        for stage in self.stages():
            if stage.order == self.current_order:
                return stage
        return None

    @property
    def is_open(self):
        return self.status in ('submitted', 'in_review')

    @property
    def can_resubmit(self):
        return self.status == 'returned'

    @property
    def fee_amount(self):
        return self.service.fee if self.service else 0

    @property
    def payment(self):
        return self.payments.first()

    def can_act(self, user):
        if not getattr(user, 'is_authenticated', False):
            return False
        if user.is_superuser or user.can('city.manage'):
            return True
        stage = self.current_stage
        return bool(self.is_open and stage and user.role_id == stage.role_id)

    def field_values(self):
        rows = []
        for spec in self.form.field_specs():
            if spec['kind'] != 'field':
                continue
            label = spec['label']
            value = self.data.get(label, '')
            if not value:
                # Applications saved before typed labels were parsed kept the
                # raw line (for example "Date of birth|date") as the key.
                for raw in self.form.field_list():
                    if raw != label and raw.split('|')[0].strip() == label:
                        value = self.data.get(raw, '')
                        if value:
                            break
            rows.append((label, value))
        return rows

    def next_stage(self):
        for stage in self.stages():
            if stage.order > self.current_order:
                return stage
        return None


class ApplicationAction(models.Model):
    DECISIONS = [
        ('verify', 'Verified and forwarded'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('return', 'Returned for correction'),
        ('resubmit', 'Resubmitted by applicant'),
    ]

    application = models.ForeignKey(ServiceApplication, on_delete=models.CASCADE,
                                    related_name='actions')
    order = models.PositiveSmallIntegerField(default=1)
    label = models.CharField(max_length=80)
    role_code = models.CharField(max_length=60, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              on_delete=models.SET_NULL, related_name='application_actions')
    decision = models.CharField(max_length=20, choices=DECISIONS, default='verify')
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.application.reference} {self.decision}'


def attachment_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f'attachments/{instance.application.reference}/{uuid4().hex}{ext}'


class ApplicationAttachment(models.Model):
    application = models.ForeignKey(ServiceApplication, on_delete=models.CASCADE,
                                    related_name='attachments')
    field_label = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to=attachment_path)
    original_name = models.CharField(max_length=255)
    size = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['uploaded_at', 'id']

    def __str__(self):
        return self.original_name

    @property
    def size_kb(self):
        return max(1, round(self.size / 1024))

    @property
    def is_image(self):
        return os.path.splitext(self.original_name)[1].lower() in (
            '.jpg', '.jpeg', '.png', '.webp')


class ServicePayment(models.Model):
    METHODS = [
        ('bkash', 'bKash'),
        ('nagad', 'Nagad'),
        ('bank', 'Bank transfer'),
        ('sslcommerz', 'SSLCommerz'),
    ]

    application = models.ForeignKey(ServiceApplication, on_delete=models.CASCADE,
                                    related_name='payments')
    method = models.CharField(max_length=20, choices=METHODS)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    transaction_id = models.CharField(max_length=40, unique=True)
    payer_ref = models.CharField(max_length=25, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.transaction_id} {self.amount}'
