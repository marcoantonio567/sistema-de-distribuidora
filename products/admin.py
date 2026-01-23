from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Category, Brand, Product, ProductImage, ProductAttribute, ProductAttributeValue, ProductReview


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active', 'products_count', 'created_at']
    list_filter = ['is_active', 'parent', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'slug', 'parent', 'description')
        }),
        ('Imagem', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )
    
    def products_count(self, obj):
        count = obj.get_products_count()
        url = reverse('admin:products_product_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}">{} produtos</a>', url, count)
    products_count.short_description = 'Produtos'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_main', 'order']
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" height="100" />')
        return "Sem imagem"
    image_preview.short_description = 'Prévia'


class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1
    fields = ['attribute', 'value']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'brand', 'price', 'stock_quantity', 'is_active', 'is_featured', 'created_at']
    list_filter = ['is_active', 'is_featured', 'category', 'brand', 'created_at']
    search_fields = ['name', 'description', 'sku']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    list_editable = ['price', 'stock_quantity', 'is_active', 'is_featured']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'slug', 'sku', 'category', 'brand', 'short_description', 'description')
        }),
        ('Preço e Estoque', {
            'fields': ('price', 'stock_quantity')
        }),
        ('Dimensões e Peso', {
            'fields': ('weight', 'length', 'width', 'height'),
            'classes': ('collapse',)
        }),
        ('Status e Visibilidade', {
            'fields': ('is_active', 'is_featured', 'created_at', 'updated_at')
        }),
    )
    
    inlines = [ProductImageInline, ProductAttributeValueInline]
    
    def image_preview(self, obj):
        main_image = obj.get_main_image()
        if main_image:
            return mark_safe(f'<img src="{main_image.image.url}" width="200" height="200" />')
        return "Sem imagem principal"
    image_preview.short_description = 'Imagem Principal'


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Logo', {
            'fields': ('logo',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_at')
        }),
    )


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user_name', 'rating', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating', 'created_at']
    search_fields = ['user_name', 'user_email', 'comment']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Informações do Cliente', {
            'fields': ('user_name', 'user_email')
        }),
        ('Avaliação', {
            'fields': ('product', 'rating', 'comment')
        }),
        ('Moderação', {
            'fields': ('is_approved', 'created_at')
        }),
    )
    
    actions = ['approve_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f'{queryset.count()} avaliações aprovadas.')
    approve_reviews.short_description = 'Aprovar avaliações selecionadas'