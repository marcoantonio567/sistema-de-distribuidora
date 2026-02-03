from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, View, DetailView
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Q, Sum, Count, F
from django.contrib.auth.models import User
from django.db.models.functions import TruncDate
from django.utils import timezone
from .models import Product, Category, Brand
from .forms import ProductForm, ProductImageInlineFormSet
from orders.models import Order, OrderItem, Coupon, OrderStatusHistory
from accounts.models import UserProfile
from orders.forms import CouponForm
from django.http import JsonResponse
import json


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = reverse_lazy('accounts:login')

    def test_func(self):
        return self.request.user.is_staff


class CategoryCreateAPIView(StaffRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            name = data.get('name')
            if not name:
                return JsonResponse({'error': 'Nome é obrigatório'}, status=400)
            
            category = Category.objects.create(name=name)
            return JsonResponse({
                'id': category.id,
                'name': category.name,
                'success': True
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class CategoryDeleteAPIView(StaffRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            category = get_object_or_404(Category, pk=pk)
            # Check if it has products
            if category.product_set.exists():
                return JsonResponse({'error': 'Não é possível excluir: existem produtos nesta categoria.'}, status=400)
            
            # Check if it has children
            if category.children.exists():
                 return JsonResponse({'error': 'Não é possível excluir: existem subcategorias associadas.'}, status=400)

            category.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class PainelHomeView(StaffRequiredMixin, TemplateView):
    template_name = 'painel/base_painel.html'

class SalesDashboardView(StaffRequiredMixin, TemplateView):
    template_name = 'painel/relatorios/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        valid_status = ['processing', 'out_for_delivery', 'completed']
        orders_qs = Order.objects.filter(status__in=valid_status)
        top_products = (
            OrderItem.objects.filter(order__status__in=valid_status)
            .values('product_id', 'product__name')
            .annotate(total_qty=Sum('quantity'), total_revenue=Sum(F('subtotal')))
            .order_by('-total_qty')[:10]
        )
        top_customers = (
            orders_qs.filter(user__isnull=False)
            .values('user_id', 'user__username')
            .annotate(order_count=Count('id'), total_spent=Sum('total_amount'))
            .order_by('-order_count')[:10]
        )
        total_revenue = orders_qs.aggregate(total=Sum('total_amount'))['total'] or 0
        total_orders = orders_qs.count()
        avg_ticket = (total_revenue / total_orders) if total_orders else 0
        today = timezone.now().date()
        since = today - timezone.timedelta(days=30)
        revenue_by_day = (
            orders_qs.filter(created_at__date__gte=since)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(total=Sum('total_amount'), count=Count('id'))
            .order_by('day')
        )
        recent_orders = orders_qs.filter(created_at__date=today).select_related('user').annotate(total_items=Sum('items__quantity')).order_by('-created_at')
        
        # Prepare data for charts
        revenue_data_list = list(revenue_by_day)
        revenue_labels = [d['day'].strftime('%d/%m') for d in revenue_data_list]
        revenue_values = [float(d['total']) for d in revenue_data_list]
        
        prod_data = list(top_products)
        prod_labels = [p['product__name'] for p in prod_data]
        prod_values = [p['total_qty'] for p in prod_data]
        
        cust_data = list(top_customers)
        cust_labels = [c['user__username'] for c in cust_data]
        cust_values = [float(c['total_spent']) for c in cust_data]

        ctx.update({
            'top_products': top_products,
            'top_customers': top_customers,
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'avg_ticket': avg_ticket,
            'revenue_by_day': list(revenue_by_day),
            'recent_orders': recent_orders,
            # JSON for charts
            'chart_revenue_labels': json.dumps(revenue_labels),
            'chart_revenue_values': json.dumps(revenue_values),
            'chart_prod_labels': json.dumps(prod_labels),
            'chart_prod_values': json.dumps(prod_values),
            'chart_cust_labels': json.dumps(cust_labels),
            'chart_cust_values': json.dumps(cust_values),
        })
        return ctx

class ProductAdminListView(StaffRequiredMixin, ListView):
    model = Product
    template_name = 'painel/produtos/list.html'
    context_object_name = 'produtos'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('category', 'brand')
        q = self.request.GET.get('q')
        categoria = self.request.GET.get('categoria')
        marca = self.request.GET.get('marca')
        ativo = self.request.GET.get('ativo')

        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q))
        if categoria:
            qs = qs.filter(category_id=categoria)
        if marca:
            qs = qs.filter(brand_id=marca)
        if ativo:
            is_active = ativo == '1'
            qs = qs.filter(is_active=is_active)
        
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.all()
        ctx['brands'] = Brand.objects.all()
        return ctx

class ProductAdminCreateView(StaffRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'painel/produtos/form.html'
    success_url = reverse_lazy('painel:produtos_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['inlines'] = ProductImageInlineFormSet(self.request.POST, self.request.FILES)
        else:
            ctx['inlines'] = ProductImageInlineFormSet()
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        inlines = ctx['inlines']
        if inlines.is_valid():
            self.object = form.save()
            inlines.instance = self.object
            inlines.save()
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class ProductAdminUpdateView(StaffRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'painel/produtos/form.html'
    success_url = reverse_lazy('painel:produtos_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['inlines'] = ProductImageInlineFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            ctx['inlines'] = ProductImageInlineFormSet(instance=self.object)
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        inlines = ctx['inlines']
        if inlines.is_valid():
            self.object = form.save()
            inlines.instance = self.object
            inlines.save()
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class ProductAdminDeleteView(StaffRequiredMixin, DeleteView):
    model = Product
    template_name = 'painel/produtos/confirm_delete.html'
    success_url = reverse_lazy('painel:produtos_list')

class ProductToggleActiveView(StaffRequiredMixin, View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.is_active = not product.is_active
        product.save()
        return redirect('painel:produtos_list')

class ProductToggleFeaturedView(StaffRequiredMixin, View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.is_featured = not product.is_featured
        product.save()
        return redirect('painel:produtos_list')

class ProductAdjustStockView(StaffRequiredMixin, View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        quantity = int(request.POST.get('quantity', 0))
        operation = request.POST.get('operation') # 'add', 'subtract', 'set'
        
        if operation == 'add':
            product.stock_quantity += quantity
        elif operation == 'subtract':
            product.stock_quantity = max(0, product.stock_quantity - quantity)
        elif operation == 'set':
            product.stock_quantity = max(0, quantity)
            
        product.save(update_fields=['stock_quantity'])
        return redirect('painel:produtos_list')

# Coupon Views

class CouponAdminListView(StaffRequiredMixin, ListView):
    model = Coupon
    template_name = 'painel/cupons/list.html'
    context_object_name = 'coupons'
    paginate_by = 20
    ordering = ['-valid_to']

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(code__icontains=q)
        return qs

class CouponAdminCreateView(StaffRequiredMixin, CreateView):
    model = Coupon
    form_class = CouponForm
    template_name = 'painel/cupons/form.html'
    success_url = reverse_lazy('painel:cupons_list')

class CouponAdminUpdateView(StaffRequiredMixin, UpdateView):
    model = Coupon
    form_class = CouponForm
    template_name = 'painel/cupons/form.html'
    success_url = reverse_lazy('painel:cupons_list')

class CouponAdminDeleteView(StaffRequiredMixin, DeleteView):
    model = Coupon
    template_name = 'painel/cupons/confirm_delete.html'
    success_url = reverse_lazy('painel:cupons_list')

class CouponToggleActiveView(StaffRequiredMixin, View):
    def post(self, request, pk):
        coupon = get_object_or_404(Coupon, pk=pk)
        coupon.active = not coupon.active
        coupon.save()
        return redirect('painel:cupons_list')

# Order Management Views

class OrderAdminListView(StaffRequiredMixin, ListView):
    model = Order
    template_name = 'painel/orders/list.html'
    context_object_name = 'orders'
    paginate_by = 20
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset().select_related('user')
        q = self.request.GET.get('q')
        status = self.request.GET.get('status')
        
        if q:
            qs = qs.filter(
                Q(order_number__icontains=q) |
                Q(customer_name__icontains=q) |
                Q(customer_email__icontains=q)
            )
        
        if status:
            qs = qs.filter(status=status)
            
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.STATUS_CHOICES
        context['q'] = self.request.GET.get('q', '')
        context['f_status'] = self.request.GET.get('status', '')
        return context

class OrderAdminDetailView(StaffRequiredMixin, DetailView):
    model = Order
    template_name = 'painel/orders/detail.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'

    def get_queryset(self):
        return super().get_queryset().prefetch_related('items__product', 'status_history', 'shipping_address')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.STATUS_CHOICES
        return context

class OrderUpdateStatusView(StaffRequiredMixin, View):
    def post(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if new_status and new_status != order.status:
            order.update_status(new_status, notes)
            
        return redirect('painel:orders_detail', order_number=order.order_number)

class ClientAdminListView(StaffRequiredMixin, ListView):
    model = User
    template_name = 'painel/clientes/list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        qs = User.objects.filter(is_superuser=False).select_related('profile')
        q = self.request.GET.get('q')
        
        if q:
            qs = qs.filter(
                Q(username__icontains=q) |
                Q(email__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(profile__phone__icontains=q)
            )
            
        qs = qs.annotate(
            order_count=Count('order'),
            total_spent=Sum('order__total_amount', filter=Q(order__status='completed'))
        ).order_by('-date_joined')
        
        return qs

class ClientAdminDetailView(StaffRequiredMixin, DetailView):
    model = User
    template_name = 'painel/clientes/detail.html'
    context_object_name = 'client'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        
        # Last orders
        context['last_orders'] = Order.objects.filter(user=user).order_by('-created_at')[:10]
        
        # Stats
        context['total_orders'] = Order.objects.filter(user=user).count()
        context['completed_orders'] = Order.objects.filter(user=user, status='completed').count()
        context['total_spent'] = Order.objects.filter(user=user, status='completed').aggregate(sum=Sum('total_amount'))['sum'] or 0
        
        return context

