from django.contrib import admin
from .models import Marca, Categoria, Produto, Combo, ComboItem, GrupoOpcao, Opcao, Pedido, EnderecoEntrega, ItemPedido, ItemOpcao

class ItemOpcaoInline(admin.TabularInline):
    model = ItemOpcao
    extra = 0

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id","nome_cliente","telefone","tipo_atendimento","status","total","criado_em")
    list_filter = ("status","tipo_atendimento","criado_em")
    search_fields = ("nome_cliente","telefone")
    inlines = [ItemPedidoInline]

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("id","nome","marca","categoria","volume_ml","embalagem","preco","estoque_atual","ativo")
    list_filter = ("categoria","marca","ativo")
    search_fields = ("nome",)

@admin.register(Combo)
class ComboAdmin(admin.ModelAdmin):
    list_display = ("id","nome","preco_combo","ativo")

admin.site.register(Marca)
admin.site.register(Categoria)
admin.site.register(ComboItem)
admin.site.register(GrupoOpcao)
admin.site.register(Opcao)
admin.site.register(EnderecoEntrega)
admin.site.register(ItemOpcao)
