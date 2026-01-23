from django.db import models
from django.contrib.sessions.models import Session
from products.models import Product
import uuid


class Cart(models.Model):
    """Shopping cart model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Carrinho'
        verbose_name_plural = 'Carrinhos'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Carrinho {self.id}"
    
    @property
    def total_items(self):
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_amount(self):
        """Get total amount of cart"""
        return sum(item.subtotal for item in self.items.all())
    
    def get_item(self, product):
        """Get cart item for a specific product"""
        try:
            return self.items.get(product=product)
        except CartItem.DoesNotExist:
            return None
    
    def add_item(self, product, quantity=1):
        """Add product to cart or update quantity if already exists"""
        if quantity <= 0:
            return False
        
        # Check if product is in stock
        if not product.is_in_stock or product.stock_quantity < quantity:
            return False
        
        item, created = self.items.get_or_create(
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Update quantity if item already exists
            new_quantity = item.quantity + quantity
            if product.stock_quantity >= new_quantity:
                item.quantity = new_quantity
                item.save()
            else:
                return False
        
        self.save()  # Update cart timestamp
        return True
    
    def remove_item(self, product):
        """Remove product from cart"""
        try:
            item = self.items.get(product=product)
            item.delete()
            self.save()
            return True
        except CartItem.DoesNotExist:
            return False
    
    def update_item_quantity(self, product, quantity):
        """Update quantity of a product in cart"""
        if quantity <= 0:
            return self.remove_item(product)
        
        try:
            item = self.items.get(product=product)
            if product.stock_quantity >= quantity:
                item.quantity = quantity
                item.save()
                self.save()
                return True
            return False
        except CartItem.DoesNotExist:
            return False
    
    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()
        self.save()
    
    def is_valid_for_checkout(self):
        """Check if cart is valid for checkout"""
        if self.total_items == 0:
            return False
        
        # Check if all products are still in stock
        for item in self.items.all():
            if not item.product.is_in_stock or item.product.stock_quantity < item.quantity:
                return False
        
        return True


class CartItem(models.Model):
    """Cart item model"""
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Carrinho'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='Produto'
    )
    quantity = models.PositiveIntegerField('Quantidade', default=1)
    added_at = models.DateTimeField('Adicionado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Item do Carrinho'
        verbose_name_plural = 'Itens do Carrinho'
        unique_together = ['cart', 'product']
        ordering = ['added_at']
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
    
    @property
    def subtotal(self):
        """Get subtotal for this item"""
        return self.product.price * self.quantity
    
    def save(self, *args, **kwargs):
        # Ensure quantity is not greater than available stock
        if self.quantity > self.product.stock_quantity:
            self.quantity = self.product.stock_quantity
        super().save(*args, **kwargs)