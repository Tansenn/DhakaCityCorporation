from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Payment(models.Model):
    STATUS = [
        ('initiated', 'Initiated'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE,
                                related_name='payments')
    txn_id = models.CharField(max_length=60, unique=True)
    gateway = models.CharField(max_length=60, default='Demo gateway')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS, default='initiated')
    receipt_no = models.CharField(max_length=60, blank=True)
    signature = models.CharField(max_length=128, blank=True)
    raw = models.JSONField(default=dict, blank=True)
    initiated_at = models.DateTimeField(default=timezone.now)
    verified_at = models.DateTimeField(null=True, blank=True)
    refunded_amount = models.DecimalField(max_digits=10, decimal_places=2,
                                          default=Decimal('0'))
    refunded_at = models.DateTimeField(null=True, blank=True)
    is_sample = models.BooleanField(default=True)

    class Meta:
        ordering = ['-initiated_at']

    def __str__(self):
        return self.txn_id

    @property
    def is_settled(self):
        return self.status == 'success' and self.verified_at is not None


class PaymentCallback(models.Model):
    RESULT = [
        ('confirmed', 'Payment confirmed'),
        ('failed', 'Payment failed'),
        ('cancelled', 'Payment cancelled'),
        ('duplicate', 'Duplicate callback ignored'),
        ('rejected', 'Rejected - invalid signature'),
        ('mismatch', 'Rejected - amount or reference mismatch'),
    ]
    payment = models.ForeignKey(Payment, null=True, blank=True,
                                on_delete=models.SET_NULL, related_name='callbacks')
    txn_id = models.CharField(max_length=60, blank=True)
    signature = models.CharField(max_length=128, blank=True)
    signature_valid = models.BooleanField(default=False)
    kind = models.CharField(max_length=20, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    result = models.CharField(max_length=20, choices=RESULT, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']


class Refund(models.Model):
    STATUS = [
        ('requested', 'Requested'),
        ('processed', 'Processed'),
        ('rejected', 'Rejected'),
    ]
    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE,
                                related_name='refunds')
    payment = models.ForeignKey(Payment, null=True, blank=True,
                                on_delete=models.SET_NULL, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))
    reason = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='requested')
    gateway_ref = models.CharField(max_length=60, blank=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='+')
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='+')
    created_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Refund {self.booking.reference} {self.amount}'
