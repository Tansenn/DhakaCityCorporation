from django.urls import path

from . import views

urlpatterns = [
    path('notifications/', views.my_notifications, name='my_notifications'),
    path('outbox/', views.outbox, name='outbox'),
    path('outbox/templates/', views.templates, name='notification_templates'),
]
