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
    list_display = ['order_number', 'customer_name', 'customer_email', 'total_amount_display', 'status_badge', 'created_at']
    list_filter = ['status', 'created_at', 'updated_at']
    search_fields = ['order_number', 'customer_name', 'customer_email', 'customer_phone']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'total_amount_display', 'get_total_items']
    inlines = [ShippingAddressInline, OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Informações do Pedido', {
            'fields': ('order_number', 'status', 'created_at', 'updated_at')
        }),
        ('Cliente', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Valores', {
            'fields': ('subtotal', 'shipping_cost', 'total_amount_display')
        }),
        ('Informações Adicionais', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_confirmed', 'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered']
    
    def total_amount_display(self, obj):
        return f"R$ {obj.total_amount:.2f}"
    total_amount_display.short_description = 'Valor Total'
    
    def status_badge(self, obj):
        status_colors = {
            'pending': 'warning',
            'confirmed': 'info',
            'processing': 'primary',
            'shipped': 'secondary',
            'delivered': 'success',
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
    
    def mark_as_confirmed(self, request, queryset):
        for order in queryset:
            if order.status == 'pending':
                order.update_status('confirmed', 'Status alterado pelo administrador')
        self.message_user(request, f'{queryset.count()} pedido(s) marcado(s) como confirmado(s).')
    mark_as_confirmed.short_description = 'Marcar como Confirmado'
    
    def mark_as_processing(self, request, queryset):
        for order in queryset:
            if order.status in ['pending', 'confirmed']:
                order.update_status('processing', 'Status alterado pelo administrador')
        self.message_user(request, f'{queryset.count()} pedido(s) marcado(s) como em processamento.')
    mark_as_processing.short_description = 'Marcar como Em Processamento'
    
    def mark_as_shipped(self, request, queryset):
        for order in queryset:
            if order.status == 'processing':
                order.update_status('shipped', 'Status alterado pelo administrador')
        self.message_user(request, f'{queryset.count()} pedido(s) marcado(s) como enviado(s).')
    mark_as_shipped.short_description = 'Marcar como Enviado'
    
    def mark_as_delivered(self, request, queryset):
        for order in queryset:
            if order.status == 'shipped':
                order.update_status('delivered', 'Status alterado pelo administrador')
        self.message_user(request, f'{queryset.count()} pedido(s) marcado(s) como entregue(s).')
    mark_as_delivered.short_description = 'Marcar como Entregue'


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ['order', 'full_address', 'city', 'state', 'zip_code']
    list_filter = ['state', 'city']
    search_fields = ['order__order_number', 'street', 'neighborhood', 'city', 'state']
    readonly_fields = ['full_address']
    
    def full_address(self, obj):
        return obj.full_address
    full_address.short_description = 'Endereço Completo'