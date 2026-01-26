from django import forms
from django.forms import inlineformset_factory
from django.utils.text import slugify
from .models import Product, ProductImage


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'sku', 'category', 'brand',
            'short_description', 'description',
            'price', 'stock_quantity', 'unit',
            'weight', 'length', 'width', 'height',
            'is_active', 'is_featured',
        ]

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        name = self.cleaned_data.get('name')
        if not slug and name:
            slug = slugify(name)
        return slug


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_main', 'order']


ProductImageInlineFormSet = inlineformset_factory(
    parent_model=Product,
    model=ProductImage,
    form=ProductImageForm,
    fields=['image', 'alt_text', 'is_main', 'order'],
    extra=1,
    can_delete=True
)
