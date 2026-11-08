from django.urls import path

from . import views

urlpatterns = [
    path('documents/', views.register, name='documents_register'),
    path('documents/files/', views.files, name='documents_files'),
    path('documents/overdue/', views.overdue, name='documents_overdue'),
    path('documents/access/', views.access_log, name='documents_access'),
    path('documents/<int:pk>/', views.file_detail, name='documents_file'),
]
