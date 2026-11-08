from django.urls import path

from . import views

urlpatterns = [
    path('mis/', views.executive, name='mis_executive'),
    path('mis/department/', views.department_dashboard, name='mis_department'),
    path('mis/bookings/', views.booking_report, name='mis_bookings'),
    path('mis/reports/', views.report_library, name='mis_reports'),
    path('mis/reports/export/', views.report_export, name='mis_report_export'),
    path('mis/access-log/', views.access_log, name='mis_access_log'),
]
