from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect

EXEMPT_PREFIXES = (
    '/login/', '/logout/', '/register/', '/verify-email/', '/resend-otp/',
    '/demo/switch/', '/lang/', '/admin/',
)


class DemoSessionMiddleware:
    """Session language, read-only role enforcement and health counters."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.session.get('gzp_lang'):
            request.session['gzp_lang'] = 'en'

        user = getattr(request, 'user', None)
        if (
            user is not None and user.is_authenticated and user.is_read_only
            and request.method not in ('GET', 'HEAD', 'OPTIONS')
            and not any(request.path.startswith(p) for p in EXEMPT_PREFIXES)
        ):
            messages.error(
                request,
                'This account has read-only access (Management / Auditor). '
                'No changes were saved.',
            )
            referer = request.META.get('HTTP_REFERER')
            return redirect(referer or '/app/')

        response = self.get_response(request)

        if response.status_code >= 500:
            try:
                from core.models import HealthEvent
                HealthEvent.objects.create(
                    kind='error',
                    message=f'HTTP {response.status_code}',
                    path=request.path[:255],
                )
            except Exception:
                pass
        return response
