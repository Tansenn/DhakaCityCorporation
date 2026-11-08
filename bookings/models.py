from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils import timezone

from core.utils import next_reference

STATUSES = [
    ('submitted', 'Submitted'),
    ('under_review', 'Under Review'),
    ('clarification', 'Clarification Required'),
    ('recommended', 'Recommended'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('awaiting_payment', 'Awaiting Payment'),
    ('paid', 'Paid / Confirmed'),
    ('cancelled', 'Cancelled'),
    ('completed', 'Completed'),
    ('expired', 'Payment window expired'),
]
STATUS_LABELS = dict(STATUSES)
OPEN_STATUSES = ['submitted', 'under_review', 'clarification', 'recommended',
                 'approved', 'awaiting_payment']
LIVE_STATUSES = OPEN_STATUSES + ['paid']


class Booking(models.Model):
    CATEGORIES = [
        ('government', 'Government official'),
        ('citizen', 'Public citizen'),
        ('organization', 'Organization'),
    ]
    SLOTS = [
        ('', 'Full day / overnight'),
        ('morning', 'Morning (09:00-13:00)'),
        ('afternoon', 'Afternoon (13:00-17:00)'),
        ('evening', 'Evening (17:00-21:00)'),
    ]

    reference = models.CharField(max_length=40, unique=True, blank=True)
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='bookings')
    facility = models.ForeignKey('facilities.Facility', on_delete=models.PROTECT,
                                 related_name='bookings')
    unit = models.ForeignKey('facilities.Unit', on_delete=models.PROTECT,
                             related_name='bookings')
    category = models.CharField(max_length=20, choices=CATEGORIES, default='citizen')
    check_in = models.DateField()
    check_out = models.DateField()
    slot = models.CharField(max_length=12, choices=SLOTS, blank=True, default='')
    guests = models.PositiveIntegerField(default=1)
    purpose = models.CharField(max_length=255)
    contact_phone = models.CharField(max_length=30, blank=True)
    notes = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUSES, default='submitted')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    deposit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    gateway_charge = models.DecimalField(max_digits=10, decimal_places=2,
                                         default=Decimal('0'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    price_breakdown = models.JSONField(default=list, blank=True,
                                       encoder=DjangoJSONEncoder)

    hold_expires_at = models.DateTimeField(null=True, blank=True)
    payment_deadline = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.CharField(max_length=255, blank=True)

    permit_no = models.CharField(max_length=40, blank=True)
    permit_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    permit_issued_at = models.DateTimeField(null=True, blank=True)

    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                      on_delete=models.SET_NULL, related_name='checkins')

    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.CharField(max_length=255, blank=True)
    cancelled_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='+')

    refund_status = models.CharField(max_length=20, default='none',
                                     choices=[('none', 'Not requested'),
                                              ('requested', 'Refund requested'),
                                              ('processed', 'Refund processed'),
                                              ('rejected', 'Refund rejected')])
    refund_percent = models.DecimalField(max_digits=5, decimal_places=2,
                                         default=Decimal('0'))
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2,
                                        default=Decimal('0'))
    refund_requested_at = models.DateTimeField(null=True, blank=True)

    is_sample = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.reference

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = next_reference('GZP-DB', Booking, 'reference')
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------ helpers
    @property
    def applicant_name(self):
        return self.applicant.get_full_name() or self.applicant.username

    @property
    def is_hall(self):
        return self.unit.is_hall

    @property
    def nights(self):
        return max(1, (self.check_out - self.check_in).days)

    @property
    def status_label(self):
        return STATUS_LABELS.get(self.status, self.status)

    @property
    def can_pay(self):
        return (self.status == 'awaiting_payment'
                and (self.payment_deadline is None
                     or self.payment_deadline > timezone.now()))

    @property
    def payment(self):
        return self.payments.filter(status='success').order_by('-verified_at').first()

    @property
    def payment_txn_id(self):
        payment = self.payment
        return payment.txn_id if payment else ''

    @property
    def days_until_checkin(self):
        return (self.check_in - timezone.localdate()).days

    @property
    def status_rank(self):
        order = [s[0] for s in STATUSES]
        return order.index(self.status) if self.status in order else 0

    @property
    def workflow_instance(self):
        from workflow.models import WorkflowInstance

        return WorkflowInstance.objects.filter(
            object_type='bookings.Booking', object_id=self.pk
        ).order_by('-created_at').first()

    def set_status(self, status, actor=None, comment=''):
        if status == self.status:
            return
        BookingStatusChange.objects.create(
            booking=self, from_status=self.status, to_status=status,
            actor=actor, comment=comment,
        )
        self.status = status
        self.save(update_fields=['status', 'updated_at'])

    def timeline(self):
        """Citizen timeline: status changes plus submission."""
        rows = [{
            'status': 'submitted', 'label': 'Submitted',
            'at': self.created_at, 'actor': self.applicant_name,
            'comment': 'Application received',
        }]
        for change in self.status_changes.order_by('created_at'):
            rows.append({
                'status': change.to_status,
                'label': STATUS_LABELS.get(change.to_status, change.to_status),
                'at': change.created_at,
                'actor': change.actor.display_name if change.actor else 'System',
                'comment': change.comment,
            })
        return rows

    def on_workflow_decision(self, decision, instance):
        """Called by the workflow engine after every decision."""
        from facilities import availability

        if decision in ('correct', 'return'):
            self.set_status('clarification', comment=instance.note or 'Correction requested')
            return
        if decision == 'reject':
            self.set_status('rejected', comment=instance.note or 'Rejected')
            self.rejected_at = timezone.now()
            self.rejection_reason = instance.note[:255]
            self.save(update_fields=['rejected_at', 'rejection_reason'])
            availability.release_booking_locks(self)
            self.hold_expires_at = None
            self.save(update_fields=['hold_expires_at'])
            return

        if instance.status == 'approved':
            if self.status in ('paid', 'completed', 'cancelled', 'expired'):
                return
            self.approved_at = timezone.now()
            self.status = 'approved'
            self.save(update_fields=['approved_at', 'status', 'updated_at'])
            self.set_status('awaiting_payment',
                            comment='Approved. Payment can now be completed.')
            self.payment_deadline = availability.resolve_payment_window(self)
            availability.confirm_locks(self, until=self.payment_deadline)
            self.hold_expires_at = self.payment_deadline
            self.save(update_fields=['payment_deadline', 'hold_expires_at',
                                     'updated_at'])
            return

        # intermediate forward / recommend decisions
        if decision == 'recommend':
            self.set_status('recommended', comment='Recommended by the reviewing officer')
        else:
            self.set_status('under_review', comment='Review in progress')
        self.hold_expires_at = (timezone.now() + timedelta(hours=48)
                                if self.workflow_instance else None)
        self.save(update_fields=['hold_expires_at'])


class BookingStatusChange(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE,
                                related_name='status_changes')
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              on_delete=models.SET_NULL, related_name='+')
    comment = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']


class BookingDocument(models.Model):
    KINDS = [
        ('supporting', 'Supporting document'),
        ('evidence', 'Clarification evidence'),
        ('receipt', 'Gateway receipt'),
        ('permit', 'Permit'),
    ]
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE,
                                related_name='documents')
    label = models.CharField(max_length=120)
    file = models.FileField(upload_to='bookings/%Y/%m/')
    kind = models.CharField(max_length=20, choices=KINDS, default='supporting')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='+')
    uploaded_at = models.DateTimeField(default=timezone.now)
    is_sample = models.BooleanField(default=True)

    class Meta:
        ordering = ['-uploaded_at']


class BookingMessage(models.Model):
    """Message thread between the citizen and the booking desk."""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE,
                                related_name='messages')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                               on_delete=models.SET_NULL, related_name='+')
    body = models.TextField()
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']
