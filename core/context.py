from django.conf import settings

from core import i18n


def global_context(request):
    from core.assets import ASSETS
    from accounts.nav import build_nav
    from accounts.demo import city_demo_accounts
    from core.models import get_setting
    from notifications.models import Notification
    from organizations.models import Organization

    app_name = get_setting('app_name', settings.APP_NAME)
    app_main, _, app_sub = app_name.partition(':')

    lang = 'en'
    try:
        lang = request.session.get('gzp_lang', 'en')
    except AttributeError:
        pass
    user = getattr(request, 'user', None)
    authenticated = bool(user and user.is_authenticated)

    org = None
    try:
        org = (Organization.objects.filter(code='dscc', is_active=True).first()
               or Organization.objects.filter(is_active=True).first())
    except Exception:
        org = None

    if org and org.is_city:
        app_main = org.name_bn if lang == 'bn' and org.name_bn else org.name
        app_sub = (org.title_bn if lang == 'bn' and org.title_bn else org.title)
        title_local = app_sub
    elif org:
        _, _, subtitle = org.title.partition(':')
        title_local = subtitle.strip() or org.title
    else:
        title_local = app_sub.strip() or 'Integrated Digital Service Platform'

    unread = 0
    nav_groups = []
    if authenticated:
        unread = Notification.objects.filter(
            user=user, channel='inapp', read_at__isnull=True
        ).count()
        nav_groups = build_nav(user, org)

    return {
        'APP_NAME': app_name,
        'APP_NAME_MAIN': i18n.translate(app_main.strip() or app_name, lang),
        'APP_NAME_SUB': i18n.translate(app_sub.strip() or 'Integrated Digital Service Platform', lang),
        'ORG': org,
        'ORG_NAME': org.name if org else settings.ORGANISATION,
        'ORG_NAME_LOCAL': ((org.name_bn if lang == 'bn' and org.name_bn else org.name)
                           if org else settings.ORGANISATION),
        'ORG_TITLE_LOCAL': title_local,
        'ORG_HEAD_TITLE': org.head_title if org else '',
        'ORG_HEAD_NAME': org.head_name if org else '',
        'ORG_IS_CITY': bool(org and org.is_city),
        'ORG_HOME': '/dscc/',
        'SUPPLIER': settings.SUPPLIER,
        'DEMO_MODE': settings.DEMO_MODE,
        'lang': lang,
        'is_bn': lang == 'bn',
        'nav_groups': nav_groups,
        'unread_count': unread,
        'demo_accounts': city_demo_accounts() if settings.DEMO_MODE else [],
        'global_today': None,
        'asset_categories': ASSETS,
    }
