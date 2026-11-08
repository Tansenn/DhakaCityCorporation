from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('', include('accounts.urls')),
    path('', include('bookings.urls')),
    path('', include('payments.urls')),
    path('app/', include('workflow.urls')),
    path('app/', include('facilities.urls')),
    path('app/', include('hr.urls')),
    path('app/', include('documents.urls')),
    path('app/', include('projects.urls')),
    path('app/', include('meetings.urls')),
    path('app/', include('mis.urls')),
    path('app/', include('support.urls')),
    path('app/', include('notifications.urls')),
    path('app/', include('audit.urls')),
]

handler403 = 'core.views.error_403'
handler404 = 'core.views.error_404'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
