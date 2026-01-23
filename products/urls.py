from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('category/<slug:category_slug>/', views.ProductListView.as_view(), name='category_products'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    
    # AJAX endpoints
    path('api/search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('api/submit-review/<slug:slug>/', views.submit_review, name='submit_review'),
]