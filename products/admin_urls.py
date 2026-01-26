from django.urls import path
from . import admin_views

app_name = 'painel'

urlpatterns = [
    path('', admin_views.PainelHomeView.as_view(), name='home'),
    path('produtos/', admin_views.ProductAdminListView.as_view(), name='produtos_list'),
    path('produtos/novo/', admin_views.ProductAdminCreateView.as_view(), name='produtos_create'),
    path('produtos/<int:pk>/editar/', admin_views.ProductAdminUpdateView.as_view(), name='produtos_update'),
    path('produtos/<int:pk>/excluir/', admin_views.ProductAdminDeleteView.as_view(), name='produtos_delete'),
    path('produtos/<int:pk>/ativar/', admin_views.ProductToggleActiveView.as_view(), name='produtos_toggle_active'),
    path('produtos/<int:pk>/destaque/', admin_views.ProductToggleFeaturedView.as_view(), name='produtos_toggle_featured'),
    path('produtos/<int:pk>/estoque/ajustar/', admin_views.ProductAdjustStockView.as_view(), name='produtos_adjust_stock'),
]
