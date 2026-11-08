from django.urls import path

from . import views

urlpatterns = [
    path('projects/', views.project_list, name='projects_list'),
    path('projects/inspections/', views.inspections, name='projects_inspections'),
    path('projects/<int:pk>/', views.project_detail, name='projects_detail'),
]
