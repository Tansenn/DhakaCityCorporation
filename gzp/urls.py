from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path('', include('organizations.urls')),
    path('', include('core.urls')),
    path('', include('services.urls')),
    path('', include('accounts.urls')),
    path('app/', include('notifications.urls')),
    path('app/', include('audit.urls')),
]

handler403 = 'core.views.error_403'
handler404 = 'core.views.error_404'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
