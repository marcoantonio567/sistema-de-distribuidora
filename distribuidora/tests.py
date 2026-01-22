from django.test import TestCase
from .models import Categoria, Marca, Produto, Pedido, ItemPedido
from .forms import CheckoutForm
from decimal import Decimal

class TelefoneValidationTest(TestCase):
    def test_telefone_invalido(self):
        form = CheckoutForm(data={
            "nome_cliente":"Teste",
            "telefone":"123",  # curto demais
            "tipo_atendimento":"retirada"
        })
        self.assertFalse(form.is_valid())

    def test_telefone_valido(self):
        form = CheckoutForm(data={
            "nome_cliente":"Teste",
            "telefone":"+5511999999999",
            "tipo_atendimento":"retirada"
        })
        self.assertTrue(form.is_valid())

class CalculoPedidoTest(TestCase):
    def test_subtotal_total(self):
        cat = Categoria.objects.create(nome="Cervejas")
        marca = Marca.objects.create(nome="MarcaX")
        prod = Produto.objects.create(categoria=cat, marca=marca, nome="Lager", volume_ml=350, embalagem="lata", unidades_por_pacote=1, preco=Decimal("5.50"), ativo=True, estoque_atual=10)
        ped = Pedido.objects.create(nome_cliente="Cliente", telefone="+5511999999999", tipo_atendimento="retirada", total=Decimal("0"), status="novo")
        item = ItemPedido.objects.create(pedido=ped, produto=prod, quantidade=2, preco_unitario=prod.preco, subtotal=Decimal("11.00"))
        total = sum(i.subtotal for i in ped.itens.all())
        self.assertEqual(total, Decimal("11.00"))
