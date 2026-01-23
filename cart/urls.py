from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.CartView.as_view(), name='cart_detail'),
    path('add/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('remove/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('update/', views.UpdateCartItemView.as_view(), name='update_cart_item'),
    path('clear/', views.ClearCartView.as_view(), name='clear_cart'),
    path('summary/', views.cart_summary, name='cart_summary'),
]