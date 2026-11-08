from django.urls import path

from . import views

urlpatterns = [
    path('hr/', views.dashboard, name='hr_dashboard'),
    path('hr/employees/', views.employees, name='hr_employees'),
    path('hr/employees/<int:pk>/', views.employee_detail, name='hr_employee'),
    path('hr/attendance/', views.attendance, name='hr_attendance'),
    path('hr/leave/', views.leave, name='hr_leave'),
    path('hr/roster/', views.roster, name='hr_roster'),
    path('hr/training/', views.training, name='hr_training'),
]
