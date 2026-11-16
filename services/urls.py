from django.urls import path

from . import views

urlpatterns = [
    path('dscc/', views.city_home, name='city_home'),
    path('dscc/services/<slug:code>/', views.city_service, name='city_service'),
    path('dscc/forms/', views.city_forms, name='city_forms'),
    path('dscc/offices/', views.city_offices, name='city_offices'),
    path('dscc/acts/', views.city_acts, name='city_acts'),
    path('dscc/forms/<int:pk>/', views.city_form, name='city_form'),
    path('dscc/forms/<int:pk>/fill/', views.city_form_fill, name='city_form_fill'),
    path('dscc/applications/', views.city_applications, name='city_applications'),
    path('dscc/applications/<str:ref>/', views.city_application, name='city_application'),
    path('dscc/applications/<str:ref>/attachments/<int:pk>/', views.city_attachment,
         name='city_attachment'),
    path('dscc/applications/<str:ref>/pay/', views.city_payment, name='city_payment'),
    path('dscc/applications/<str:ref>/pdf/', views.city_application_pdf,
         name='city_application_pdf'),
    path('dscc/applications/<str:ref>/certificate.pdf', views.city_certificate,
         name='city_certificate'),
    path('dscc/applications/<str:ref>/resubmit/', views.city_resubmit, name='city_resubmit'),
    path('app/city/', views.city_dashboard, name='city_dashboard'),
    path('app/city/queue/', views.city_queue, name='city_queue'),
    path('app/city/applications/<str:ref>/action/', views.city_action, name='city_action'),
    path('app/city/setup/', views.city_setup, name='city_setup'),

    path('services/forms/<int:pk>/<str:variant>/', views.form_download, name='form_download'),
]
