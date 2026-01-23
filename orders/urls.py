from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('success/<slug:order_number>/', views.OrderSuccessView.as_view(), name='order_success'),
    path('detail/<slug:order_number>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('list/', views.OrderListView.as_view(), name='order_list'),
    path('cancel/<slug:order_number>/', views.CancelOrderView.as_view(), name='cancel_order'),
    path('tracking/<slug:order_number>/', views.order_tracking, name='order_tracking'),
]