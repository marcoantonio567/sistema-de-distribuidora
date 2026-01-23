from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from .models import Category, Product, Brand, ProductReview
import logging

logger = logging.getLogger('products')


class ProductListView(ListView):
    """View for listing products with filtering and search"""
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category', 'brand').prefetch_related('images')
        
        # Category filter
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug, is_active=True)
            # Include products from subcategories
            categories = [category] + list(category.get_children())
            queryset = queryset.filter(category__in=categories)
        
        # Brand filter
        brand_slug = self.request.GET.get('brand')
        if brand_slug:
            queryset = queryset.filter(brand__slug=brand_slug)
        
        # Price filter
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Search query
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(short_description__icontains=search_query)
            )
        
        # Sorting
        sort = self.request.GET.get('sort', 'created_at')
        if sort == 'price_low':
            queryset = queryset.order_by('price')
        elif sort == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort == 'name':
            queryset = queryset.order_by('name')
        else:  # newest
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Categories for filter sidebar
        context['categories'] = Category.objects.filter(is_active=True, parent=None)
        
        # Brands for filter
        context['brands'] = Brand.objects.filter(is_active=True)
        
        # Current filters
        context['current_category'] = self.kwargs.get('category_slug')
        context['current_brand'] = self.request.GET.get('brand')
        context['min_price'] = self.request.GET.get('min_price')
        context['max_price'] = self.request.GET.get('max_price')
        context['search_query'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', 'created_at')
        
        # Price range for filter
        active_products = Product.objects.filter(is_active=True)
        if active_products.exists():
            context['min_product_price'] = active_products.order_by('price').first().price
            context['max_product_price'] = active_products.order_by('-price').first().price
        
        return context


@method_decorator(cache_page(60 * 15), name='get')  # Cache for 15 minutes
class ProductDetailView(DetailView):
    """View for product details"""
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category', 'brand').prefetch_related('images', 'attribute_values__attribute', 'reviews')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        
        # Product images
        context['images'] = product.get_all_images()
        
        # Related products (same category)
        context['related_products'] = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:4]
        
        # Product attributes
        context['attributes'] = product.attribute_values.all()
        
        # Reviews
        context['reviews'] = product.reviews.filter(is_approved=True)
        context['average_rating'] = product.reviews.filter(is_approved=True).aggregate(avg=Avg('rating'))['avg'] or 0
        context['review_count'] = product.reviews.filter(is_approved=True).count()
        
        # Breadcrumb
        context['breadcrumb'] = self.get_breadcrumb(product.category)
        
        return context
    
    def get_breadcrumb(self, category):
        """Generate breadcrumb for category hierarchy"""
        breadcrumb = []
        current = category
        while current:
            breadcrumb.insert(0, current)
            current = current.parent
        return breadcrumb


class CategoryListView(ListView):
    """View for listing categories"""
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.filter(is_active=True, parent=None).prefetch_related('children')


@require_http_methods(["GET"])
def search_suggestions(request):
    """AJAX endpoint for search suggestions"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    try:
        products = Product.objects.filter(
            is_active=True,
            name__icontains=query
        )[:5]
        
        suggestions = [
            {
                'name': product.name,
                'url': product.get_absolute_url(),
                'image': product.get_main_image().image.url if product.get_main_image() else None,
                'price': str(product.price)
            }
            for product in products
        ]
        
        return JsonResponse({'suggestions': suggestions})
    except Exception as e:
        logger.error(f"Error in search suggestions: {e}")
        return JsonResponse({'suggestions': []})


@require_http_methods(["POST"])
def submit_review(request, slug):
    """Submit a product review"""
    try:
        product = get_object_or_404(Product, slug=slug, is_active=True)
        
        user_name = request.POST.get('user_name')
        user_email = request.POST.get('user_email')
        rating = int(request.POST.get('rating', 0))
        comment = request.POST.get('comment', '')
        
        if not all([user_name, user_email, rating, comment]):
            return JsonResponse({'success': False, 'error': 'Todos os campos são obrigatórios.'})
        
        if rating < 1 or rating > 5:
            return JsonResponse({'success': False, 'error': 'Avaliação deve estar entre 1 e 5.'})
        
        # Check if user already reviewed this product
        if ProductReview.objects.filter(product=product, user_email=user_email).exists():
            return JsonResponse({'success': False, 'error': 'Você já avaliou este produto.'})
        
        review = ProductReview.objects.create(
            product=product,
            user_name=user_name,
            user_email=user_email,
            rating=rating,
            comment=comment
        )
        
        return JsonResponse({'success': True, 'message': 'Avaliação enviada com sucesso!'})
    
    except Exception as e:
        logger.error(f"Error submitting review: {e}")
        return JsonResponse({'success': False, 'error': 'Erro ao enviar avaliação.'})