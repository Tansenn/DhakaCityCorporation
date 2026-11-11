from django.conf import settings

from core import i18n


def global_context(request):
    from core.assets import ASSETS
    from accounts.nav import build_nav
    from accounts.demo import demo_accounts
    from core.models import get_setting
    from notifications.models import Notification

    app_name = get_setting('app_name', settings.APP_NAME)
    app_main, _, app_sub = app_name.partition(':')

    lang = 'en'
    try:
        lang = request.session.get('gzp_lang', 'en')
    except AttributeError:
        pass
    user = getattr(request, 'user', None)
    authenticated = bool(user and user.is_authenticated)

    unread = 0
    nav_groups = []
    if authenticated:
        unread = Notification.objects.filter(
            user=user, channel='inapp', read_at__isnull=True
        ).count()
        nav_groups = build_nav(user)

    return {
        'APP_NAME': app_name,
        'APP_NAME_MAIN': i18n.translate(app_main.strip() or app_name, lang),
        'APP_NAME_SUB': i18n.translate(app_sub.strip() or 'Integrated Digital Platform', lang),
        'ORG_NAME': settings.ORGANISATION,
        'SUPPLIER': settings.SUPPLIER,
        'DEMO_MODE': settings.DEMO_MODE,
        'lang': lang,
        'is_bn': lang == 'bn',
        'nav_groups': nav_groups,
        'unread_count': unread,
        'demo_accounts': demo_accounts() if settings.DEMO_MODE else [],
        'global_today': None,
        'asset_categories': ASSETS,
    }
