from django.urls import path

from . import views, catalogue

urlpatterns = [
    path('', catalogue.catalogue, name='home'),
    path('user/', catalogue.catalogue, name='user_home'),
    path('user/assets/<int:pk>/', catalogue.asset_detail, name='asset_detail'),
    path('track/', views.track, name='track'),
    path('verify/<uuid:token>/', views.verify_permit, name='verify_permit'),
    path('lang/<str:code>/', views.set_language, name='set_language'),
    path('app/', views.dashboard, name='dashboard'),
    path('app/settings/', views.settings_page, name='settings'),
    path('app/security/', views.security_page, name='security'),
    path('app/health/', views.health_page, name='health'),
]
