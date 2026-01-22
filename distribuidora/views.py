from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from .models import Categoria, Produto, Combo, Opcao, GrupoOpcao, Pedido, ItemPedido, ItemOpcao, EnderecoEntrega
from .forms import CheckoutForm

def _get_cart(request):
    cart = request.session.get("cart", {"itens": [], "tipo_atendimento": "retirada"})
    request.session["cart"] = cart
    return cart

def _cart_total(cart):
    total = Decimal("0.00")
    for item in cart["itens"]:
        total += Decimal(str(item["subtotal"]))
    return total

def kiosk_home(request):
    cart = _get_cart(request)
    return render(request, "kiosk/home.html", {"cart": cart})

def kiosk_categorias(request):
    categorias = Categoria.objects.filter(ativa=True).order_by("nome")
    return render(request, "kiosk/categorias.html", {"categorias": categorias})

def kiosk_produtos(request):
    categoria_id = request.GET.get("categoria")
    marca_id = request.GET.get("marca")
    qs = Produto.objects.filter(ativo=True)
    if categoria_id:
        qs = qs.filter(categoria_id=categoria_id)
    if marca_id:
        qs = qs.filter(marca_id=marca_id)
    produtos = qs.order_by("marca__nome", "nome")
    return render(request, "kiosk/produtos.html", {"produtos": produtos})

def kiosk_produto_opcoes(request, produto_id):
    produto = get_object_or_404(Produto, pk=produto_id, ativo=True)
    grupos = list(produto.grupos_opcao.all()) + list(produto.categoria.grupos_opcao.all())
    return render(request, "kiosk/produto_opcoes.html", {"produto": produto, "grupos": grupos})

def kiosk_combos(request):
    combos = Combo.objects.filter(ativo=True).order_by("nome")
    return render(request, "kiosk/combos.html", {"combos": combos})

def kiosk_carrinho(request):
    cart = _get_cart(request)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_produto":
            produto_id = int(request.POST["produto_id"])
            quantidade = int(request.POST.get("quantidade", "1"))
            produto = get_object_or_404(Produto, pk=produto_id, ativo=True)
            if produto.estoque_atual < quantidade:
                messages.error(request, "Estoque insuficiente para este produto.")
                return redirect("kiosk_produtos")
            subtotal = Decimal(str(produto.preco)) * quantidade
            cart["itens"].append({
                "tipo": "produto",
                "produto_id": produto.id,
                "nome": f"{produto.marca.nome} {produto.nome}",
                "quantidade": quantidade,
                "preco_unitario": str(produto.preco),
                "opcoes": [],
                "subtotal": str(subtotal),
            })
        elif action == "add_combo":
            combo_id = int(request.POST["combo_id"])
            combo = get_object_or_404(Combo, pk=combo_id, ativo=True)
            cart["itens"].append({
                "tipo": "combo",
                "combo_id": combo.id,
                "nome": combo.nome,
                "quantidade": 1,
                "preco_unitario": str(combo.preco_combo),
                "opcoes": [],
                "subtotal": str(combo.preco_combo),
            })
        elif action == "remove":
            idx = int(request.POST["index"])
            if 0 <= idx < len(cart["itens"]):
                cart["itens"].pop(idx)
        request.session.modified = True
        return redirect("kiosk_carrinho")
    total = _cart_total(cart)
    return render(request, "kiosk/carrinho.html", {"cart": cart, "total": total})

def kiosk_checkout(request):
    cart = _get_cart(request)
    if not cart["itens"]:
        messages.error(request, "Seu carrinho está vazio.")
        return redirect("kiosk_categorias")
    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            cart["tipo_atendimento"] = form.cleaned_data["tipo_atendimento"]
            request.session["checkout"] = form.cleaned_data
            request.session.modified = True
            return redirect("kiosk_confirmacao")
    else:
        form = CheckoutForm(initial={"tipo_atendimento": cart.get("tipo_atendimento", "retirada")})
    total = _cart_total(cart)
    return render(request, "kiosk/checkout.html", {"form": form, "cart": cart, "total": total})

@transaction.atomic
def kiosk_confirmacao(request):
    cart = _get_cart(request)
    checkout = request.session.get("checkout")
    if not cart["itens"] or not checkout:
        return redirect("kiosk_categorias")
    if request.method == "POST":
        pedido = Pedido.objects.create(
            nome_cliente=checkout["nome_cliente"],
            telefone=checkout["telefone"],
            tipo_atendimento=checkout["tipo_atendimento"],
            observacoes=checkout.get("observacoes",""),
            total=_cart_total(cart),
            status="novo",
        )
        if checkout["tipo_atendimento"] == "entrega":
            EnderecoEntrega.objects.create(
                pedido=pedido,
                rua=checkout.get("rua",""),
                numero=checkout.get("numero",""),
                bairro=checkout.get("bairro",""),
                referencia=checkout.get("referencia",""),
            )
        for item in cart["itens"]:
            if item["tipo"] == "produto":
                produto = Produto.objects.select_for_update().get(pk=item["produto_id"])
                if produto.estoque_atual < item["quantidade"]:
                    messages.error(request, f"Estoque insuficiente para {produto}.")
                    transaction.set_rollback(True)
                    return redirect("kiosk_carrinho")
                produto.estoque_atual -= item["quantidade"]
                produto.save()
                ip = ItemPedido.objects.create(
                    pedido=pedido,
                    produto=produto,
                    quantidade=item["quantidade"],
                    preco_unitario=Decimal(str(item["preco_unitario"])),
                    subtotal=Decimal(str(item["subtotal"])),
                )
                for op in item.get("opcoes", []):
                    op_model = Opcao.objects.get(pk=op["opcao_id"])
                    ItemOpcao.objects.create(item_pedido=ip, opcao=op_model, preco_extra=Decimal(str(op.get("preco_extra","0"))))
            elif item["tipo"] == "combo":
                # itens de combo não decrementam estoque individualmente neste MVP
                pass
        request.session["cart"] = {"itens": [], "tipo_atendimento": "retirada"}
        request.session.pop("checkout", None)
        messages.success(request, f"Pedido #{pedido.id} criado com sucesso!")
        return redirect("kiosk_home")
    total = _cart_total(cart)
    return render(request, "kiosk/confirmacao.html", {"cart": cart, "checkout": checkout, "total": total})

def is_staff(user):
    return user.is_staff

@user_passes_test(is_staff, login_url="/admin/login/")
def painel_pedidos(request):
    status = request.GET.get("status")
    tipo = request.GET.get("tipo_atendimento")
    pedidos = Pedido.objects.all().order_by("-criado_em")
    if status:
        pedidos = pedidos.filter(status=status)
    if tipo:
        pedidos = pedidos.filter(tipo_atendimento=tipo)
    return render(request, "painel/pedidos.html", {"pedidos": pedidos})

@user_passes_test(is_staff, login_url="/admin/login/")
def painel_pedido_detalhe(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    return render(request, "painel/pedido_detalhe.html", {"pedido": pedido})

@user_passes_test(is_staff, login_url="/admin/login/")
def painel_pedido_status(request, pedido_id, novo_status):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    pedido.status = novo_status
    pedido.save()
    messages.success(request, f"Status do Pedido #{pedido.id} atualizado para {novo_status}.")
    return redirect(reverse("painel_pedido_detalhe", args=[pedido.id]))
