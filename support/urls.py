from django.urls import path

from . import views

urlpatterns = [
    path('support/', views.tickets, name='support_tickets'),
    path('support/<int:pk>/', views.ticket_detail, name='support_ticket'),
    path('acceptance/', views.acceptance, name='support_acceptance'),
    path('acceptance/checklists/', views.checklists, name='support_checklists'),
    path('change-requests/', views.change_requests, name='support_changes'),
]
