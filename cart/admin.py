from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'subtotal', 'added_at']
    can_delete = True
    
    def subtotal(self, obj):
        return f"R$ {obj.subtotal:.2f}"
    subtotal.short_description = 'Subtotal'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_key_short', 'total_items', 'total_amount_display', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['session_key', 'id']
    readonly_fields = ['id', 'created_at', 'updated_at', 'total_items', 'total_amount_display']
    inlines = [CartItemInline]
    
    fieldsets = (
        ('Informações do Carrinho', {
            'fields': ('id', 'session_key', 'created_at', 'updated_at')
        }),
        ('Resumo', {
            'fields': ('total_items', 'total_amount_display')
        }),
    )
    
    def session_key_short(self, obj):
        return f"{obj.session_key[:8]}..." if len(obj.session_key) > 8 else obj.session_key
    session_key_short.short_description = 'Chave da Sessão'
    
    def total_amount_display(self, obj):
        return f"R$ {obj.total_amount:.2f}"
    total_amount_display.short_description = 'Valor Total'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'subtotal_display', 'added_at']
    list_filter = ['added_at', 'cart__created_at']
    search_fields = ['product__name', 'cart__session_key']
    readonly_fields = ['subtotal_display', 'added_at']
    
    def subtotal_display(self, obj):
        return f"R$ {obj.subtotal:.2f}"
    subtotal_display.short_description = 'Subtotal'