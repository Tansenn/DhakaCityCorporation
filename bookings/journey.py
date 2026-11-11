"""Plain-language status journey for a booking.

The route comes from the workflow template, so the tracker always matches the
steps and roles that are actually configured in the workflow designer.
"""
from __future__ import annotations

from workflow.engine import applicable_steps
from workflow.models import WorkflowTemplate

ROLE_SHORT = {
    'bookingdesk': 'Booking desk',
    'engineer': 'Technical reviewer',
    'eo': 'Executive Officer',
    'ceo': 'CEO / Chairman',
    'reception': 'Reception desk',
    'finance': 'Finance officer',
}

ROLE_STAGE = {
    'bookingdesk': 'Booking desk review',
    'engineer': 'Technical review',
    'eo': 'Executive Officer approval',
    'ceo': 'CEO / Chairman approval',
    'reception': 'Reception check',
    'finance': 'Finance check',
}

ROLE_DUTY = {
    'bookingdesk': 'Checks the application and documents',
    'engineer': 'Checks the room or hall is ready',
    'eo': 'Approves within the delegated limit',
    'ceo': 'Gives the final approval',
    'reception': 'Checks the permit at the desk',
    'finance': 'Confirms the payment',
}

MINE_INSTRUCTION = {
    'bookingdesk': 'This application is at your desk. Check the documents and forward it.',
    'engineer': 'This application is at your desk. Check the room or hall and recommend it.',
    'eo': 'This application is at your desk. Approve within the delegated limit or forward it.',
    'ceo': 'This application is at your desk. Give the final approval or reject it.',
}

ADVANCE_DECISIONS = ('forward', 'recommend', 'approve')


def role_short(role):
    if role is None:
        return ''
    return ROLE_SHORT.get(role.code, role.name)


def role_duty(role):
    if role is None:
        return ''
    return ROLE_DUTY.get(role.code, 'Reviews this application')


def stage_label(role, fallback):
    if role is None:
        return fallback
    return ROLE_STAGE.get(role.code, fallback)


def _stage(key, label, state, role=None, duty='', extra=None):
    stage = {
        'key': key,
        'label': label,
        'state': state,
        'role_name': role.name if role else '',
        'role_short': role_short(role),
        'role_code': role.code if role else '',
        'duty': duty or role_duty(role),
        'actor': '',
        'when': None,
        'decision': '',
        'note': '',
        'is_mine': False,
    }
    if extra:
        stage.update(extra)
    return stage


def build_journey(booking, user=None):
    """Return the visible stages with done / current / waiting / stopped states."""
    instance = booking.workflow_instance
    status = booking.status
    stages = [_stage('submitted', 'Application received', 'done',
                     extra={'actor': booking.applicant_name, 'when': booking.created_at})]

    current = None
    if instance:
        records = {}
        for record in instance.records.select_related('actor', 'step').order_by('created_at'):
            if record.step_id:
                records[record.step_id] = record
        stopped = instance.status in ('rejected', 'cancelled')
        for step in applicable_steps(instance.template, instance.payload):
            record = records.get(step.pk)
            done = bool(record and record.decision in ADVANCE_DECISIONS)
            rejected_here = bool(record and record.decision == 'reject')
            is_current = instance.current_step_id == step.pk and instance.status in (
                'running', 'returned')
            if done:
                state = 'done'
            elif rejected_here:
                state = 'stopped'
            elif is_current:
                state = 'current'
            elif stopped:
                state = 'skipped'
            else:
                state = 'waiting'
            extra = {
                'actor': record.actor.display_name if record and record.actor else '',
                'when': record.created_at if record else None,
                'decision': record.get_decision_display() if record else '',
                'note': record.comments if record else '',
            }
            stage = _stage(f'step-{step.pk}', stage_label(step.role, step.name), state,
                           role=step.role, extra=extra)
            if state == 'current':
                stage['is_mine'] = bool(
                    user and user.is_authenticated and user.role_id == step.role_id)
                current = stage
            stages.append(stage)

    approved = (instance.status == 'approved' if instance else
                status in ('approved', 'awaiting_payment', 'paid', 'completed'))
    payment = booking.payment
    payment_done = bool(payment)
    if (booking.payment_flow == 'direct' or payment_done or approved
            or status in ('awaiting_payment', 'paid', 'completed', 'expired')):
        pay_state = 'done' if payment_done else (
            'current' if booking.can_pay else 'waiting')
        payment_stage = _stage(
            'payment', 'Payment', pay_state,
            duty='Payment received' if payment_done else 'Complete payment on the demo gateway',
            extra={
                'actor': booking.applicant_name if payment_done else '',
                'when': payment.verified_at if payment else None,
            },
        )
        stages.append(payment_stage)
        if pay_state == 'current' and (approved or current is None):
            current = payment_stage

    permit_done = bool(approved and booking.permit_issued_at)
    if permit_done:
        permit_state = 'done'
    elif status in ('rejected', 'cancelled', 'expired'):
        permit_state = 'skipped'
    else:
        permit_state = 'waiting'
    stages.append(_stage(
        'permit', 'Permit issued', permit_state,
        duty='Download and show the permit at reception',
        extra={'actor': booking.applicant_name if permit_done else '',
               'when': booking.permit_issued_at},
    ))

    if status in ('rejected', 'cancelled', 'expired'):
        for stage in stages:
            if stage['state'] in ('waiting', 'current'):
                stage['state'] = 'skipped'
        current = None

    is_staff = bool(user and user.is_authenticated and getattr(
        user, 'is_staff_portal_user', False))

    if status == 'rejected':
        instruction = 'The application was rejected. See the approval history for the reason.'
        instruction_key = 'rejected'
    elif status == 'cancelled':
        instruction = 'The application was cancelled. You can apply again for another date.'
        instruction_key = 'cancelled'
    elif status == 'expired':
        instruction = 'The payment window closed. The hold was released; please apply again.'
        instruction_key = 'expired'
    elif status == 'completed':
        instruction = 'The stay is complete. Thank you for using the Dakbungalow.'
        instruction_key = 'completed'
    elif status == 'paid' and permit_done:
        instruction = 'Approved and paid. Your permit is ready to download and show at reception.'
        instruction_key = 'paid'
    elif instance and instance.status == 'returned':
        if payment_done:
            instruction = 'Payment received. A correction was requested. Reply in the message section below.'
            instruction_key = 'payment_received_returned'
        else:
            instruction = 'A correction was requested. Reply in the message section below.'
            instruction_key = 'returned'
    elif payment_done and not approved:
        instruction = 'Payment received. Approval is pending; your permit will be available after final approval.'
        instruction_key = 'payment_received'
    elif payment_done:
        instruction = 'Payment received and approval complete. Please contact the booking desk to confirm your permit.'
        instruction_key = 'payment_received_unconfirmed'
    elif booking.payment_flow == 'direct' and booking.can_pay and not approved:
        instruction = 'You can pay now on the demo gateway. Your permit will be issued only after final approval.'
        instruction_key = 'direct_payment'
    elif status == 'awaiting_payment':
        instruction = 'Your application is approved. Pay on the demo gateway to confirm the booking.'
        instruction_key = 'payment'
    elif current is not None and current.get('is_mine'):
        instruction = MINE_INSTRUCTION.get(current['role_code'],
                                          'This application is at your desk.')
        instruction_key = 'mine'
    elif current is not None:
        instruction = 'Waiting for the next officer to review this application.'
        instruction_key = 'waiting'
    elif approved:
        instruction = 'All approval steps are complete. Payment is next.'
        instruction_key = 'approved'
    else:
        instruction = 'Your application is in the queue. The booking desk will review it next.'
        instruction_key = 'queue'

    return {
        'stages': stages,
        'current': current,
        'instruction': instruction,
        'instruction_key': instruction_key,
        'is_staff': is_staff,
    }


def booking_route(user=None):
    """The configured booking approval route, marked with the viewer's own desk."""
    template = WorkflowTemplate.objects.filter(code='booking', is_active=True).first()
    if template is None:
        return []
    rows = []
    for step in template.steps.select_related('role').order_by('order'):
        rows.append({
            'order': step.order,
            'label': stage_label(step.role, step.name),
            'role_name': step.role.name,
            'role_short': role_short(step.role),
            'role_code': step.role.code,
            'duty': role_duty(step.role),
            'sla_hours': step.sla_hours,
            'is_mine': bool(user and getattr(user, 'role_id', None) == step.role_id),
            'decisions': step.allowed_decisions or [],
        })
    return rows
