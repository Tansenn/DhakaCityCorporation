from django.urls import path

from . import views

urlpatterns = [
    path('pay/<str:txn_id>/', views.gateway_checkout, name='gateway_checkout'),
    path('pay/<str:txn_id>/callback/', views.gateway_action, name='gateway_callback'),
    path('app/payments/', views.payment_list, name='payment_list'),
    path('app/payments/export.csv', views.payment_export, name='payment_export'),
    path('app/payments/release-holds/', views.release_holds, name='release_holds'),
    path('app/refunds/', views.refund_list, name='refund_list'),
    path('app/refunds/<int:pk>/action/', views.refund_action, name='refund_action'),
]
