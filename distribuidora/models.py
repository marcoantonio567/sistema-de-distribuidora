from django.db import models

class Marca(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.nome

class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    ativa = models.BooleanField(default=True)
    def __str__(self):
        return self.nome

class Produto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="produtos")
    marca = models.ForeignKey(Marca, on_delete=models.PROTECT, related_name="produtos")
    nome = models.CharField(max_length=120)
    volume_ml = models.PositiveIntegerField(null=True, blank=True)
    embalagem = models.CharField(max_length=50, blank=True)
    unidades_por_pacote = models.PositiveIntegerField(default=1)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    ativo = models.BooleanField(default=True)
    estoque_atual = models.PositiveIntegerField(default=0)
    def __str__(self):
        return f"{self.marca} {self.nome}"

class Combo(models.Model):
    nome = models.CharField(max_length=120)
    ativo = models.BooleanField(default=True)
    preco_combo = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self):
        return self.nome

class ComboItem(models.Model):
    combo = models.ForeignKey(Combo, on_delete=models.CASCADE, related_name="itens")
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField(default=1)

class GrupoOpcao(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name="grupos_opcao", null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name="grupos_opcao", null=True, blank=True)
    nome = models.CharField(max_length=120)
    tipo = models.CharField(max_length=10, choices=(("unica","única"), ("multipla","múltipla")))
    obrigatorio = models.BooleanField(default=False)
    def __str__(self):
        return self.nome

class Opcao(models.Model):
    grupo = models.ForeignKey(GrupoOpcao, on_delete=models.CASCADE, related_name="opcoes")
    nome = models.CharField(max_length=120)
    preco_extra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ativo = models.BooleanField(default=True)
    def __str__(self):
        return self.nome

class Pedido(models.Model):
    TIPO_ATENDIMENTO = (("retirada","retirada"),("entrega","entrega"))
    STATUS = (("novo","novo"),("em_preparo","em_preparo"),("pronto","pronto"),("entregue","entregue"),("cancelado","cancelado"))
    nome_cliente = models.CharField(max_length=120)
    telefone = models.CharField(max_length=20)
    tipo_atendimento = models.CharField(max_length=10, choices=TIPO_ATENDIMENTO, default="retirada")
    observacoes = models.CharField(max_length=255, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=12, choices=STATUS, default="novo")
    criado_em = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Pedido #{self.id} - {self.nome_cliente}"

class EnderecoEntrega(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name="endereco")
    rua = models.CharField(max_length=120)
    numero = models.CharField(max_length=10)
    bairro = models.CharField(max_length=80)
    referencia = models.CharField(max_length=120, blank=True)

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="itens")
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

class ItemOpcao(models.Model):
    item_pedido = models.ForeignKey(ItemPedido, on_delete=models.CASCADE, related_name="opcoes")
    opcao = models.ForeignKey(Opcao, on_delete=models.PROTECT)
    preco_extra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
