"""Small builders for tests. Keeps every test independent of the demo seed."""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from accounts.models import Permission, Role, User
from bookings.models import Booking
from facilities.models import Facility, Tariff, Unit
from workflow.models import AuthorityMatrix, WorkflowStep, WorkflowTemplate


def permission(code):
    module = code.split('.')[0]
    return Permission.objects.get_or_create(
        code=code, defaults={'label': code, 'module': module})[0]


def role(code, name=None, perms=(), read_only=False):
    obj, _ = Role.objects.get_or_create(
        code=code,
        defaults={'name': name or code.title(), 'is_read_only': read_only},
    )
    if read_only:
        obj.is_read_only = True
        obj.save(update_fields=['is_read_only'])
    for code_ in perms:
        obj.permissions.add(permission(code_))
    return obj


def user(username, role_obj, password='Test@12345', facility=None):
    return User.objects.create_user(
        username=username, password=password, role=role_obj,
        email=f'{username}@example.test', email_verified=True, facility=facility,
    )


def facility(code='test-facility'):
    return Facility.objects.create(
        code=code, name=f'Test facility {code}', location='Test location')


def unit(fac, code='R1', kind='room', amount='1500.00', deposit='1000.00'):
    obj = Unit.objects.create(
        facility=fac, code=code, name=f'Test {kind} {code}', kind=kind,
        capacity=10 if kind == 'hall' else 2,
    )
    for category in ('government', 'citizen', 'organization'):
        Tariff.objects.create(
            unit=obj, category=category, amount=Decimal(amount),
            holiday_amount=Decimal(amount) + Decimal('200'),
            deposit=Decimal(deposit),
        )
    return obj


def booking(applicant, unit_obj, days=2, status='submitted', amount='5500.00', **kwargs):
    start = timezone.localdate() + timedelta(days=kwargs.pop('start_days', 5))
    return Booking.objects.create(
        applicant=applicant, facility=unit_obj.facility, unit=unit_obj,
        category=kwargs.pop('category', 'citizen'), check_in=start,
        check_out=start + timedelta(days=days),
        purpose=kwargs.pop('purpose', 'Test purpose'),
        status=status, amount=Decimal(amount),
        deposit=Decimal('1000.00'), total=Decimal(amount), **kwargs)


def booking_template():
    template = WorkflowTemplate.objects.create(
        code='booking', name='Booking approval', category='booking')
    desk = role('bookingdesk', 'Booking Desk')
    engineer = role('engineer', 'Technical Reviewer')
    eo = role('eo', 'Executive Officer')
    ceo = role('ceo', 'CEO')
    WorkflowStep.objects.create(
        template=template, order=1, name='Booking desk review', role=desk,
        allowed_decisions=['forward', 'correct', 'reject'])
    WorkflowStep.objects.create(
        template=template, order=2, name='Technical review', role=engineer,
        allowed_decisions=['recommend', 'correct', 'reject'],
        condition={'unit_kind': ['suite', 'hall']})
    WorkflowStep.objects.create(
        template=template, order=3, name='EO approval', role=eo,
        allowed_decisions=['approve', 'recommend', 'reject', 'correct'])
    WorkflowStep.objects.create(
        template=template, order=4, name='CEO approval', role=ceo,
        allowed_decisions=['approve', 'reject', 'correct'],
        condition={'min_amount': 20000.01}, is_final=True)
    AuthorityMatrix.objects.create(role=eo, category='booking', can_approve=True,
                                   max_amount=Decimal('20000.00'))
    AuthorityMatrix.objects.create(role=ceo, category='booking', can_approve=True,
                                   max_amount=None)
    AuthorityMatrix.objects.create(role=desk, category='booking', can_approve=False)
    AuthorityMatrix.objects.create(role=engineer, category='booking', can_approve=False)
    return template
