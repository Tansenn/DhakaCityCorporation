from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('track/', views.track, name='track'),
    path('verify/<uuid:token>/', views.verify_permit, name='verify_permit'),
    path('lang/<str:code>/', views.set_language, name='set_language'),
    path('app/', views.dashboard, name='dashboard'),
    path('app/settings/', views.settings_page, name='settings'),
    path('app/security/', views.security_page, name='security'),
    path('app/health/', views.health_page, name='health'),
]
