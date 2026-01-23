from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    """Model for product categories with hierarchical structure"""
    name = models.CharField('Nome', max_length=100)
    slug = models.SlugField('Slug', unique=True, max_length=100)
    parent = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name='Categoria Pai'
    )
    description = models.TextField('Descrição', blank=True)
    image = models.ImageField('Imagem', upload_to='categories/', blank=True)
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('products:category_detail', kwargs={'slug': self.slug})
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_full_path(self):
        """Get the full hierarchical path of the category"""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name
    
    def get_children(self):
        """Get all child categories"""
        return Category.objects.filter(parent=self, is_active=True)
    
    def get_products_count(self):
        """Get count of active products in this category and its children"""
        from products.models import Product
        categories = [self] + list(self.get_children())
        return Product.objects.filter(category__in=categories, is_active=True).count()


class Brand(models.Model):
    """Model for product brands"""
    name = models.CharField('Nome', max_length=100, unique=True)
    slug = models.SlugField('Slug', unique=True, max_length=100)
    description = models.TextField('Descrição', blank=True)
    logo = models.ImageField('Logo', upload_to='brands/', blank=True)
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """Model for products"""
    name = models.CharField('Nome', max_length=200)
    slug = models.SlugField('Slug', unique=True, max_length=200)
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE,
        verbose_name='Categoria'
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Marca'
    )
    description = models.TextField('Descrição')
    short_description = models.CharField('Descrição Curta', max_length=255, blank=True)
    price = models.DecimalField('Preço', max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField('Quantidade em Estoque', default=0)
    sku = models.CharField('SKU', max_length=50, unique=True, blank=True)
    
    # Physical attributes
    weight = models.DecimalField('Peso (kg)', max_digits=8, decimal_places=2, null=True, blank=True)
    length = models.DecimalField('Comprimento (cm)', max_digits=8, decimal_places=2, null=True, blank=True)
    width = models.DecimalField('Largura (cm)', max_digits=8, decimal_places=2, null=True, blank=True)
    height = models.DecimalField('Altura (cm)', max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Status and visibility
    is_active = models.BooleanField('Ativo', default=True)
    is_featured = models.BooleanField('Destaque', default=False)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['brand', 'is_active']),
            models.Index(fields=['price']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'slug': self.slug})
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            self.sku = f"PROD-{self.id:06d}"
        super().save(*args, **kwargs)
    
    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock_quantity > 0
    
    def get_main_image(self):
        """Get the main product image"""
        try:
            return self.images.filter(is_main=True).first()
        except ProductImage.DoesNotExist:
            return None
    
    def get_all_images(self):
        """Get all product images"""
        return self.images.all()
    
    def get_discounted_price(self):
        """Get current price (considering discounts)"""
        # This can be extended to support discount logic
        return self.price
    
    def get_dimensions(self):
        """Get formatted dimensions"""
        if self.length and self.width and self.height:
            return f"{self.length} x {self.width} x {self.height} cm"
        return None
    
    def decrease_stock(self, quantity):
        """Decrease stock quantity"""
        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            self.save(update_fields=['stock_quantity'])
            return True
        return False
    
    def increase_stock(self, quantity):
        """Increase stock quantity"""
        self.stock_quantity += quantity
        self.save(update_fields=['stock_quantity'])


class ProductImage(models.Model):
    """Model for product images"""
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Produto'
    )
    image = models.ImageField('Imagem', upload_to='products/')
    alt_text = models.CharField('Texto Alternativo', max_length=255, blank=True)
    is_main = models.BooleanField('Imagem Principal', default=False)
    order = models.PositiveIntegerField('Ordem', default=0)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Imagem do Produto'
        verbose_name_plural = 'Imagens dos Produtos'
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"Imagem de {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one main image per product
        if self.is_main:
            ProductImage.objects.filter(product=self.product).update(is_main=False)
        super().save(*args, **kwargs)


class ProductAttribute(models.Model):
    """Model for product attributes (color, size, etc.)"""
    name = models.CharField('Nome', max_length=50)
    
    class Meta:
        verbose_name = 'Atributo'
        verbose_name_plural = 'Atributos'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ProductAttributeValue(models.Model):
    """Model for product attribute values"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='attribute_values',
        verbose_name='Produto'
    )
    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.CASCADE,
        verbose_name='Atributo'
    )
    value = models.CharField('Valor', max_length=100)
    
    class Meta:
        verbose_name = 'Valor do Atributo'
        verbose_name_plural = 'Valores dos Atributos'
        unique_together = ['product', 'attribute']
    
    def __str__(self):
        return f"{self.product.name} - {self.attribute.name}: {self.value}"


class ProductReview(models.Model):
    """Model for product reviews"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Produto'
    )
    user_name = models.CharField('Nome', max_length=100)
    user_email = models.EmailField('Email')
    rating = models.PositiveIntegerField(
        'Avaliação',
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField('Comentário')
    is_approved = models.BooleanField('Aprovado', default=False)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Avaliação'
        verbose_name_plural = 'Avaliações'
        ordering = ['-created_at']
        unique_together = ['product', 'user_email']
    
    def __str__(self):
        return f"{self.user_name} - {self.product.name} ({self.rating} estrelas)"