import random
from datetime import timedelta

from django.utils import timezone

from accounts.models import VerificationCode
from notifications.services import send


def issue_otp(user, purpose='register'):
    VerificationCode.objects.filter(
        user=user, purpose=purpose, used_at__isnull=True
    ).update(used_at=timezone.now())
    code = f'{random.SystemRandom().randint(0, 999999):06d}'
    record = VerificationCode.objects.create(
        user=user,
        purpose=purpose,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    user.otp_code = code
    user.otp_created_at = record.created_at
    user.otp_attempts = 0
    user.save(update_fields=['otp_code', 'otp_created_at', 'otp_attempts'])
    send(
        user,
        'verification',
        {
            'code': code,
            'reference': 'account verification',
            'subject': 'Your verification code',
            'body': f'Your Gazipur Zila Parishad verification code is {code}. '
                    f'It expires in 10 minutes.',
        },
        channels=['email', 'sms'],
    )
    return record


def verify_otp(user, code):
    record = VerificationCode.objects.filter(
        user=user, purpose='register', used_at__isnull=True
    ).order_by('-created_at').first()
    if record is None:
        return False, 'No active verification code. Please request a new code.'
    if record.expires_at < timezone.now():
        return False, 'This code has expired. Please request a new code.'
    if record.attempts >= 5:
        return False, 'Too many incorrect attempts. Please request a new code.'
    record.attempts += 1
    record.save(update_fields=['attempts'])
    if str(code).strip() != record.code:
        return False, 'The code you entered is incorrect.'
    record.used_at = timezone.now()
    record.save(update_fields=['used_at'])
    user.email_verified = True
    user.otp_code = ''
    user.otp_attempts = 0
    user.save(update_fields=['email_verified', 'otp_code', 'otp_attempts'])
    return True, 'Your email and mobile number are verified.'
