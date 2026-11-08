from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('profile/', views.profile_view, name='profile'),
    path('demo/switch/', views.demo_switch, name='demo_switch'),
    path('app/users/', views.users_list, name='users_list'),
    path('app/users/new/', views.user_form, name='user_create'),
    path('app/users/<int:pk>/', views.user_form, name='user_edit'),
    path('app/users/<int:pk>/toggle/', views.user_toggle, name='user_toggle'),
    path('app/roles/', views.roles_matrix, name='roles_matrix'),
]
