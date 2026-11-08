from django.urls import path

from . import views

urlpatterns = [
    path('meetings/', views.meeting_list, name='meetings_list'),
    path('meetings/actions/', views.actions, name='meetings_actions'),
    path('meetings/<int:pk>/', views.meeting_detail, name='meetings_detail'),
]
