from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Permission(models.Model):
    code = models.CharField(max_length=80, unique=True)
    label = models.CharField(max_length=160)
    module = models.CharField(max_length=60)

    class Meta:
        ordering = ['module', 'code']

    def __str__(self):
        return self.code


class Role(models.Model):
    code = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True, related_name='roles')
    is_read_only = models.BooleanField(
        default=False,
        help_text='Read-only roles cannot submit changes anywhere in the platform.',
    )
    sort_order = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class User(AbstractUser):
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL,
                             related_name='users')
    phone = models.CharField(max_length=30, blank=True)
    department = models.ForeignKey('hr.Department', null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='users')
    designation = models.ForeignKey('hr.Designation', null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='users')
    facility = models.ForeignKey('facilities.Facility', null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name='operators',
                                 help_text='Assigned facility for reception operators.')
    email_verified = models.BooleanField(default=False)
    is_demo = models.BooleanField(default=True)
    otp_code = models.CharField(max_length=8, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    otp_attempts = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['first_name', 'username']

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    @property
    def role_name(self):
        return self.role.name if self.role else 'No role'

    @property
    def is_citizen(self):
        return bool(self.role and self.role.code == 'citizen')

    @property
    def is_staff_portal_user(self):
        return bool(self.role and self.role.code != 'citizen')

    @property
    def is_read_only(self):
        return bool(self.role and self.role.is_read_only)

    def can(self, code):
        if not getattr(self, 'is_authenticated', False):
            return False
        if self.is_superuser:
            return True
        if not self.role_id:
            return False
        cache = getattr(self, '_perm_cache', None)
        if cache is None:
            cache = set(self.role.permissions.values_list('code', flat=True))
            self._perm_cache = cache
        return code in cache


class VerificationCode(models.Model):
    PURPOSE = [('register', 'Registration'), ('reset', 'Password reset')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='verification_codes')
    purpose = models.CharField(max_length=20, choices=PURPOSE, default='register')
    code = models.CharField(max_length=8)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    attempts = models.PositiveIntegerField(default=0)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def is_valid(self):
        return not self.used_at and self.expires_at > timezone.now()


class LoginAttempt(models.Model):
    username = models.CharField(max_length=150, blank=True)
    ip = models.CharField(max_length=64, blank=True)
    success = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.username} @ {self.ip} {"ok" if self.success else "fail"}'
