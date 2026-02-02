from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Order, OrderItem, OrderStatusHistory, ShippingAddress


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price', 'subtotal']
    can_delete = False
    
    def subtotal(self, obj):
        return f"R$ {obj.subtotal:.2f}"
    subtotal.short_description = 'Subtotal'


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['old_status', 'new_status', 'notes', 'created_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class ShippingAddressInline(admin.StackedInline):
    model = ShippingAddress
    extra = 0
    readonly_fields = ['full_address']
    
    def full_address(self, obj):
        return obj.full_address
    full_address.short_description = 'Endereço Completo'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer_name', 'customer_email', 'payment_method', 'total_amount_display', 'status_badge', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at', 'updated_at']
    search_fields = ['order_number', 'customer_name', 'customer_email', 'customer_phone']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'total_amount_display', 'get_total_items']
    inlines = [ShippingAddressInline, OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Informações do Pedido', {
            'fields': ('order_number', 'status', 'payment_method', 'created_at', 'updated_at')
        }),
        ('Cliente', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Valores', {
            'fields': ('subtotal', 'shipping_cost', 'coupon', 'discount_amount', 'total_amount_display')
        }),
        ('Informações Adicionais', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_processing', 'mark_as_out_for_delivery', 'mark_as_completed']
    
    def total_amount_display(self, obj):
        return f"R$ {obj.total_amount:.2f}"
    total_amount_display.short_description = 'Valor Total'
    
    def status_badge(self, obj):
        status_colors = {
            'processing': 'primary',
            'out_for_delivery': 'warning',
            'completed': 'success',
            'cancelled': 'danger'
        }
        color = status_colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def get_total_items(self, obj):
        return obj.get_total_items()
    get_total_items.short_description = 'Total de Itens'
    
    def mark_as_processing(self, request, queryset):
        updated = 0
        for order in queryset:
            if order.status != 'processing':
                order.update_status('processing', 'Status alterado pelo administrador')
                updated += 1
        self.message_user(request, f'{updated} pedido(s) marcado(s) como Em Processamento.')
    mark_as_processing.short_description = 'Marcar como Em Processamento'
    
    def mark_as_out_for_delivery(self, request, queryset):
        updated = 0
        for order in queryset:
            if order.status == 'processing':
                order.update_status('out_for_delivery', 'Status alterado pelo administrador')
                updated += 1
        self.message_user(request, f'{updated} pedido(s) marcado(s) como Em Rota de Entrega.')
    mark_as_out_for_delivery.short_description = 'Marcar como Em Rota de Entrega'
    
    def mark_as_completed(self, request, queryset):
        updated = 0
        for order in queryset:
            if order.status == 'out_for_delivery':
                order.update_status('completed', 'Status alterado pelo administrador')
                updated += 1
        self.message_user(request, f'{updated} pedido(s) marcado(s) como Concluído.')
    mark_as_completed.short_description = 'Marcar como Concluído'


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ['order', 'full_address', 'city', 'state', 'zip_code']
    list_filter = ['state', 'city']
    search_fields = ['order__order_number', 'street', 'neighborhood', 'city', 'state']
    readonly_fields = ['full_address']
    
    def full_address(self, obj):
        return obj.full_address
    full_address.short_description = 'Endereço Completo'