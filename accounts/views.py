from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from accounts.decorators import perm_required
from accounts.forms import StaffUserForm
from accounts.models import LoginAttempt, Permission, Role, User
from accounts.permissions import ROLE_PERMISSIONS
from accounts.services import issue_otp, verify_otp
from audit.models import log
from core.utils import get_client_ip, paginate


def landing_for(user):
    if not user or not user.is_authenticated:
        return '/'
    if user.is_citizen:
        return '/citizen/'
    return '/app/'


def _safe_next(request, candidate, fallback):
    if candidate and url_has_allowed_host_and_scheme(
        candidate, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return candidate
    return fallback


def _login_locked(username, ip):
    since = timezone.now() - timedelta(minutes=15)
    failures = LoginAttempt.objects.filter(
        created_at__gte=since, success=False
    ).filter(Q(username__iexact=username) | Q(ip=ip))
    return failures.count() >= 6


def login_view(request):
    if request.user.is_authenticated:
        return redirect(landing_for(request.user))
    next_url = request.GET.get('next') or request.POST.get('next') or ''
    username = ''
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        ip = get_client_ip(request)
        if not username or not password:
            messages.error(request, 'Enter your username and password.')
        elif _login_locked(username, ip):
            messages.error(
                request,
                'Too many failed attempts. Please wait 15 minutes before trying again.',
            )
        else:
            user = authenticate(request, username=username, password=password)
            LoginAttempt.objects.create(
                username=username, ip=ip, success=bool(user)
            )
            if user is None:
                messages.error(request, 'Invalid username or password.')
            elif user.role is None:
                messages.error(request, 'This account has no role assigned. Contact the administrator.')
            else:
                login(request, user)
                log(user, 'login', request=request, module='accounts')
                if not user.email_verified:
                    issue_otp(user)
                    messages.info(
                        request,
                        'For this demo the OTP is shown on the verification page and in the demo outbox.',
                    )
                    return redirect('verify_email')
                return redirect(_safe_next(request, next_url, landing_for(user)))
    return render(request, 'accounts/login.html', {
        'next': next_url, 'username': username, 'page_title': 'Sign in',
    })


def logout_view(request):
    if request.method != 'POST':
        return redirect('/')
    if request.user.is_authenticated:
        log(request.user, 'logout', request=request, module='accounts')
        logout(request)
    messages.success(request, 'You have signed out.')
    return redirect('/')


def register_view(request):
    if request.user.is_authenticated:
        return redirect(landing_for(request.user))
    values = {
        'first_name': '', 'last_name': '', 'username': '', 'email': '', 'phone': '',
    }
    if request.method == 'POST':
        values = {k: request.POST.get(k, '').strip() for k in values}
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        errors = []
        if not values['first_name'] or not values['last_name']:
            errors.append('Enter your full name.')
        if not values['username']:
            errors.append('Choose a username.')
        elif User.objects.filter(username__iexact=values['username']).exists():
            errors.append('That username is already taken.')
        if not values['email'] or '@' not in values['email']:
            errors.append('Enter a valid email address.')
        elif User.objects.filter(email__iexact=values['email']).exists():
            errors.append('An account already exists with that email address.')
        if not values['phone']:
            errors.append('Enter a mobile number (sample numbers only).')
        if password1 != password2:
            errors.append('The two passwords do not match.')
        elif password1:
            try:
                validate_password(password1)
            except ValidationError as exc:
                errors.extend(exc.messages)
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            role = Role.objects.filter(code='citizen').first()
            user = User.objects.create_user(
                username=values['username'],
                email=values['email'],
                password=password1,
                first_name=values['first_name'],
                last_name=values['last_name'],
                phone=values['phone'],
                role=role,
                email_verified=False,
            )
            issue_otp(user)
            login(request, user)
            log(user, 'create', user, 'Citizen self-registration', request)
            messages.success(
                request,
                'Account created. Enter the one-time code to verify your email and mobile.',
            )
            return redirect('verify_email')
    return render(request, 'accounts/register.html', {
        'values': values, 'page_title': 'Register',
    })


def verify_email(request):
    if not request.user.is_authenticated:
        return redirect('/login/')
    if request.user.email_verified:
        messages.info(request, 'Your account is already verified.')
        return redirect(landing_for(request.user))
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        ok, message = verify_otp(request.user, code)
        if ok:
            log(request.user, 'update', request.user, 'Email and mobile verified',
                request)
            messages.success(request, message)
            return redirect(landing_for(request.user))
        messages.error(request, message)
    return render(request, 'accounts/verify.html', {
        'page_title': 'Verify your account',
        'demo_code': request.user.otp_code,
    })


def resend_otp(request):
    if not request.user.is_authenticated:
        return redirect('/login/')
    if request.method == 'POST':
        issue_otp(request.user)
        messages.success(
            request,
            'A new code was generated. In the demo it is shown on screen and in the outbox.',
        )
    return redirect('verify_email')


def demo_switch(request):
    if not settings.DEMO_MODE:
        raise PermissionDenied('Demo sign-in is disabled.')
    if request.method != 'POST':
        return redirect('/login/')
    username = request.POST.get('username', '')
    user = User.objects.filter(username=username, is_demo=True).first()
    if user is None or user.role is None:
        messages.error(request, 'That demo account is not available. Run seed_demo first.')
        return redirect('/login/')
    login(request, user)
    log(user, 'login', request=request, module='accounts')
    messages.success(
        request,
        f'You are now signed in as {user.display_name} ({user.role.name}).',
    )
    return redirect(_safe_next(request, request.POST.get('next'), landing_for(user)))


def profile_view(request):
    if not request.user.is_authenticated:
        return redirect('/login/')
    user = request.user
    if request.method == 'POST':
        action = request.POST.get('action', 'profile')
        if action == 'password':
            current = request.POST.get('current_password', '')
            new1 = request.POST.get('new_password1', '')
            new2 = request.POST.get('new_password2', '')
            if not user.check_password(current):
                messages.error(request, 'The current password is incorrect.')
            elif new1 != new2:
                messages.error(request, 'The new passwords do not match.')
            else:
                try:
                    validate_password(new1, user)
                except ValidationError as exc:
                    messages.error(request, ' '.join(exc.messages))
                else:
                    user.set_password(new1)
                    user.save()
                    update_session_auth_hash(request, user)
                    log(user, 'update', user, 'Password changed', request)
                    messages.success(request, 'Your password has been changed.')
        else:
            email = request.POST.get('email', '').strip()
            if email and User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                messages.error(request, 'That email address is already in use.')
            else:
                user.first_name = request.POST.get('first_name', '').strip()
                user.last_name = request.POST.get('last_name', '').strip()
                user.email = email
                user.phone = request.POST.get('phone', '').strip()
                user.save()
                log(user, 'update', user, 'Profile updated', request)
                messages.success(request, 'Your profile has been updated.')
        return redirect('profile')
    return render(request, 'accounts/profile.html', {
        'page_title': 'My profile',
        'identities': request.user.verification_codes.all()[:5],
    })


@perm_required('accounts.view_users')
def users_list(request):
    q = request.GET.get('q', '').strip()
    role_code = request.GET.get('role', '')
    active = request.GET.get('active', '')
    rows = User.objects.select_related('role', 'department').all()
    if q:
        rows = rows.filter(
            Q(username__icontains=q) | Q(first_name__icontains=q)
            | Q(last_name__icontains=q) | Q(email__icontains=q)
        )
    if role_code:
        rows = rows.filter(role__code=role_code)
    if active in ('0', '1'):
        rows = rows.filter(is_active=active == '1')
    page_obj = paginate(request, rows.order_by('username'), 30)
    return render(request, 'accounts/users.html', {
        'page_obj': page_obj, 'q': q, 'role_code': role_code, 'active': active,
        'roles': Role.objects.all(), 'page_title': 'Users & roles',
    })


@perm_required('accounts.manage_users')
def user_form(request, pk=None):
    user = get_object_or_404(User, pk=pk) if pk else None
    if request.method == 'POST':
        form = StaffUserForm(request.POST, instance=user)
        if form.is_valid():
            saved = form.save()
            log(request.user, 'create' if not user else 'update', saved,
                'User account saved', request)
            messages.success(request, f'Account {saved.username} saved.')
            return redirect('users_list')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = StaffUserForm(instance=user)
    return render(request, 'accounts/user_form.html', {
        'form': form, 'account': user, 'page_title': 'New account' if not user else 'Edit account',
    })


@perm_required('accounts.manage_users')
def user_toggle(request, pk):
    if request.method != 'POST':
        return redirect('users_list')
    user = get_object_or_404(User, pk=pk)
    if user.pk == request.user.pk:
        messages.error(request, 'You cannot deactivate your own account.')
    else:
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        log(request.user, 'update', user,
            f'Account {"activated" if user.is_active else "deactivated"}', request)
        messages.success(request, f'Account {user.username} updated.')
    return redirect('users_list')


@perm_required('accounts.manage_roles')
def roles_matrix(request):
    permissions = list(Permission.objects.all())
    roles = list(Role.objects.prefetch_related('permissions').all())
    if request.method == 'POST':
        changes = []
        for role in roles:
            new_name = request.POST.get(f'name_{role.code}', '').strip()
            new_desc = request.POST.get(f'desc_{role.code}', '').strip()
            read_only = bool(request.POST.get(f'readonly_{role.code}'))
            chosen = []
            for perm in permissions:
                if request.POST.get(f'p_{role.code}_{perm.code}'):
                    if role.code == 'admin' and perm.code in (
                        'bookings.approve_eo', 'bookings.approve_ceo',
                    ):
                        continue
                    chosen.append(perm)
            if role.code in ('admin', 'management') and role.code == 'admin':
                keep = {'accounts.manage_roles', 'accounts.manage_settings',
                        'accounts.manage_users', 'accounts.view_users', 'audit.view'}
                chosen_codes = {p.code for p in chosen} | keep
                chosen = [p for p in permissions if p.code in chosen_codes]
            if role.code == 'management':
                read_only = True
            before = sorted(role.permissions.values_list('code', flat=True))
            role.name = new_name or role.name
            role.description = new_desc
            role.is_read_only = read_only
            role.save()
            role.permissions.set(chosen)
            after = sorted(role.permissions.values_list('code', flat=True))
            if before != after:
                changes.append(f'{role.code}: {len(before)} -> {len(after)} permissions')
        log(request.user, 'settings', None,
            'Role and permission matrix updated. ' + '; '.join(changes), request,
            module='accounts')
        messages.success(request, 'Roles, display names and permissions saved.')
        return redirect('roles_matrix')

    assigned = {role.code: {p.code for p in role.permissions.all()} for role in roles}
    return render(request, 'accounts/roles.html', {
        'roles': roles,
        'permissions': permissions,
        'assigned': assigned,
        'page_title': 'Users & roles',
    })
