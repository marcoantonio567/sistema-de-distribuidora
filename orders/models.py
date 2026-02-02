from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from products.models import Product
from cart.models import Cart
import uuid


class Coupon(models.Model):
    code = models.CharField('Código', max_length=50, unique=True)
    discount_percent = models.IntegerField('Desconto (%)', help_text='Porcentagem de desconto (0-100)')
    valid_from = models.DateTimeField('Válido de')
    valid_to = models.DateTimeField('Válido até')
    active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Cupom'
        verbose_name_plural = 'Cupons'

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_to


class Order(models.Model):
    """Order model"""
    STATUS_CHOICES = [
        ('processing', 'Em Processamento'),
        ('out_for_delivery', 'Em Rota de Entrega'),
        ('completed', 'Concluído'),
        ('cancelled', 'Cancelado'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Cartão de Crédito'),
        ('pix', 'PIX'),
        ('pay_on_delivery', 'Pagamento na Entrega'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField('Número do Pedido', max_length=20, unique=True, db_index=True)
    
    # User information (optional for guest checkout)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuário'
    )
    session_key = models.CharField('Chave da Sessão', max_length=40, blank=True, db_index=True)
    
    # Customer information
    customer_name = models.CharField('Nome do Cliente', max_length=100)
    customer_email = models.EmailField('Email do Cliente')
    customer_phone = models.CharField('Telefone do Cliente', max_length=20)
    
    # Order status
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='processing')
    payment_method = models.CharField('Forma de Pagamento', max_length=20, choices=PAYMENT_METHOD_CHOICES, default='credit_card')
    
    # Amounts
    subtotal = models.DecimalField('Subtotal', max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField('Frete', max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField('Desconto', max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField('Total', max_digits=10, decimal_places=2, default=0)
    
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Cupom de Desconto'
    )

    # Additional information
    notes = models.TextField('Observações', blank=True)
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['customer_email']),
        ]
    
    def __str__(self):
        return f"Pedido {self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """Generate unique order number"""
        today = timezone.now()
        date_prefix = today.strftime('%Y%m%d')
        last_order = Order.objects.filter(
            order_number__startswith=date_prefix
        ).order_by('-order_number').first()
        
        if last_order:
            last_number = int(last_order.order_number[-4:])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f"{date_prefix}{new_number:04d}"
    
    def get_absolute_url(self):
        return reverse('orders:order_detail', kwargs={'order_number': self.order_number})
    
    @property
    def status_display(self):
        """Get human-readable status"""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.status == 'processing'
    
    def can_be_modified(self):
        """Check if order can be modified"""
        return self.status == 'processing'
    
    def get_total_items(self):
        """Get total number of items in order"""
        return sum(item.quantity for item in self.items.all())
    
    def update_status(self, new_status, notes=""):
        """Update order status with optional notes"""
        old_status = self.status
        self.status = new_status
        if notes:
            self.notes = f"{self.notes}\nStatus changed from {old_status} to {new_status}: {notes}".strip()
        self.save()
        
        # Create status history entry
        OrderStatusHistory.objects.create(
            order=self,
            old_status=old_status,
            new_status=new_status,
            notes=notes
        )


class OrderItem(models.Model):
    """Order item model"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Pedido'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='Produto'
    )
    quantity = models.PositiveIntegerField('Quantidade')
    price = models.DecimalField('Preço Unitário', max_digits=10, decimal_places=2)
    subtotal = models.DecimalField('Subtotal', max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'
        ordering = ['id']
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Calculate subtotal
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    """Order status history model"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='Pedido'
    )
    old_status = models.CharField('Status Anterior', max_length=20, choices=Order.STATUS_CHOICES)
    new_status = models.CharField('Novo Status', max_length=20, choices=Order.STATUS_CHOICES)
    notes = models.TextField('Observações', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Histórico de Status'
        verbose_name_plural = 'Histórico de Status'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order.order_number}: {self.old_status} → {self.new_status}"


class ShippingAddress(models.Model):
    """Shipping address model"""
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='shipping_address',
        verbose_name='Pedido'
    )
    
    # Address fields
    street = models.CharField('Rua', max_length=255)
    number = models.CharField('Número', max_length=20)
    complement = models.CharField('Complemento', max_length=255, blank=True)
    neighborhood = models.CharField('Bairro', max_length=100)
    city = models.CharField('Cidade', max_length=100)
    state = models.CharField('Estado', max_length=50)
    zip_code = models.CharField('CEP', max_length=10)
    
    # Additional information
    reference = models.CharField('Ponto de Referência', max_length=255, blank=True)
    
    class Meta:
        verbose_name = 'Endereço de Entrega'
        verbose_name_plural = 'Endereços de Entrega'
    
    def __str__(self):
        return f"{self.street}, {self.number} - {self.city}, {self.state}"
    
    @property
    def full_address(self):
        """Get full formatted address"""
        address = f"{self.street}, {self.number}"
        if self.complement:
            address += f" - {self.complement}"
        address += f" - {self.neighborhood} - {self.city}, {self.state} - CEP: {self.zip_code}"
        if self.reference:
            address += f" ({self.reference})"
        return address