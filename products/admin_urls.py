from django.urls import path
from . import admin_views

app_name = 'painel'

urlpatterns = [
    path('', admin_views.PainelHomeView.as_view(), name='home'),
    path('relatorios/', admin_views.SalesDashboardView.as_view(), name='relatorios_dashboard'),
    path('produtos/', admin_views.ProductAdminListView.as_view(), name='produtos_list'),
    path('produtos/novo/', admin_views.ProductAdminCreateView.as_view(), name='produtos_create'),
    path('produtos/<int:pk>/editar/', admin_views.ProductAdminUpdateView.as_view(), name='produtos_update'),
    path('produtos/<int:pk>/excluir/', admin_views.ProductAdminDeleteView.as_view(), name='produtos_delete'),
    path('produtos/<int:pk>/ativar/', admin_views.ProductToggleActiveView.as_view(), name='produtos_toggle_active'),
    path('produtos/<int:pk>/destaque/', admin_views.ProductToggleFeaturedView.as_view(), name='produtos_toggle_featured'),
    path('produtos/<int:pk>/estoque/ajustar/', admin_views.ProductAdjustStockView.as_view(), name='produtos_adjust_stock'),
    
    # Cupons
    path('cupons/', admin_views.CouponAdminListView.as_view(), name='cupons_list'),
    path('cupons/novo/', admin_views.CouponAdminCreateView.as_view(), name='cupons_create'),
    path('cupons/<int:pk>/editar/', admin_views.CouponAdminUpdateView.as_view(), name='cupons_update'),
    path('cupons/<int:pk>/excluir/', admin_views.CouponAdminDeleteView.as_view(), name='cupons_delete'),
    path('cupons/<int:pk>/ativar/', admin_views.CouponToggleActiveView.as_view(), name='cupons_toggle_active'),
    
    # Pedidos
    path('pedidos/', admin_views.OrderAdminListView.as_view(), name='orders_list'),
    path('pedidos/<slug:order_number>/', admin_views.OrderAdminDetailView.as_view(), name='orders_detail'),
    path('pedidos/<slug:order_number>/status/', admin_views.OrderUpdateStatusView.as_view(), name='orders_update_status'),
]
