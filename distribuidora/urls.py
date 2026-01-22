from django.urls import path
from . import views

urlpatterns = [
    path("", views.kiosk_home, name="kiosk_home"),
    path("categorias/", views.kiosk_categorias, name="kiosk_categorias"),
    path("produtos/", views.kiosk_produtos, name="kiosk_produtos"),
    path("produto/<int:produto_id>/opcoes/", views.kiosk_produto_opcoes, name="kiosk_produto_opcoes"),
    path("combos/", views.kiosk_combos, name="kiosk_combos"),
    path("carrinho/", views.kiosk_carrinho, name="kiosk_carrinho"),
    path("checkout/", views.kiosk_checkout, name="kiosk_checkout"),
    path("confirmacao/", views.kiosk_confirmacao, name="kiosk_confirmacao"),
    path("painel/pedidos/", views.painel_pedidos, name="painel_pedidos"),
    path("painel/pedidos/<int:pedido_id>/", views.painel_pedido_detalhe, name="painel_pedido_detalhe"),
    path("painel/pedidos/<int:pedido_id>/status/<str:novo_status>/", views.painel_pedido_status, name="painel_pedido_status"),
]
