from django.urls import path

from . import views

urlpatterns = [
    path('facilities/', views.facility_list, name='facility_list'),
    path('facilities/<int:pk>/', views.facility_detail, name='facility_detail'),
    path('facilities/units/<int:pk>/delete/', views.delete_unit, name='delete_unit'),
    path('facilities/tariffs/<int:pk>/delete/', views.delete_tariff, name='delete_tariff'),
    path('facilities/release-holds/', views.release_holds, name='facility_release_holds'),
]
