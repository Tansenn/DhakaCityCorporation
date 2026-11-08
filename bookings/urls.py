from django.urls import path

from . import views

urlpatterns = [
    path('facilities/<slug:code>/', views.facility_public, name='facility_public'),

    path('citizen/', views.citizen_home, name='citizen_home'),
    path('book/details/', views.apply_details, name='apply_details'),
    path('book/<slug:code>/', views.apply_start, name='apply_start'),

    path('bookings/<int:pk>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:pk>/submitted/', views.booking_submitted, name='booking_submitted'),
    path('bookings/<int:pk>/message/', views.booking_message, name='booking_message'),
    path('bookings/<int:pk>/upload/', views.booking_upload, name='booking_upload'),
    path('bookings/<int:pk>/cancel/', views.booking_cancel, name='booking_cancel'),
    path('bookings/<int:pk>/pay/', views.start_booking_payment, name='booking_pay'),
    path('bookings/<int:pk>/receipt.pdf', views.booking_receipt, name='booking_receipt'),
    path('bookings/<int:pk>/permit.pdf', views.booking_permit, name='booking_permit'),
    path('bookings/<int:pk>/application.pdf', views.booking_quote_pdf,
         name='booking_application_pdf'),
    path('bookings/<int:pk>/qr.png', views.booking_qr, name='booking_qr'),

    path('app/bookings/', views.staff_list, name='staff_bookings'),
    path('app/bookings/export.csv', views.staff_export, name='staff_bookings_export'),
    path('app/bookings/<int:pk>/', views.staff_detail, name='staff_booking_detail'),
    path('app/bookings/<int:pk>/cancel/', views.staff_cancel, name='staff_booking_cancel'),
    path('app/reception/', views.reception_desk, name='reception_desk'),
    path('app/reception/<int:pk>/checkin/', views.reception_checkin, name='reception_checkin'),
    path('app/reception/<int:pk>/checkout/', views.reception_checkout, name='reception_checkout'),
]
