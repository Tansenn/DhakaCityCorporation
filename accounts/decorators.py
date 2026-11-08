from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def perm_required(*codes):
    """Server-side permission check. Menu visibility is never the only control."""

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not any(request.user.can(code) for code in codes):
                raise PermissionDenied(
                    'Your role does not include this permission.'
                )
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


def staff_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.is_staff_portal_user:
            raise PermissionDenied('This area is for Parishad staff accounts.')
        return view(request, *args, **kwargs)
    return wrapper


def citizen_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.is_citizen:
            raise PermissionDenied('This area is for citizen applicants. Staff should use the workspace.')
        return view(request, *args, **kwargs)
    return wrapper


def notify_denied(request, message='You do not have permission for that action.'):
    messages.error(request, message)
    return redirect(request.META.get('HTTP_REFERER') or '/app/')
