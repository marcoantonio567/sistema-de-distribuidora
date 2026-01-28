from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, View
from django.shortcuts import redirect
from django.db.models import Q, Sum, Count, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from .models import Product, Category, Brand
from .forms import ProductForm, ProductImageInlineFormSet
from orders.models import Order, OrderItem


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = reverse_lazy('accounts:login')

    def test_func(self):
        return self.request.user.is_staff


class PainelHomeView(StaffRequiredMixin, TemplateView):
    template_name = 'painel/base_painel.html'

class SalesDashboardView(StaffRequiredMixin, TemplateView):
    template_name = 'painel/relatorios/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        valid_status = ['confirmed', 'processing', 'shipped', 'delivered']
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
        recent_orders = orders_qs.select_related('user').order_by('-created_at')[:10]
        ctx.update({
            'top_products': top_products,
            'top_customers': top_customers,
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'avg_ticket': avg_ticket,
            'revenue_by_day': list(revenue_by_day),
            'recent_orders': recent_orders,
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
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(sku__icontains=q))
        if categoria:
            qs = qs.filter(category_id=categoria)
        if marca:
            qs = qs.filter(brand_id=marca)
        if ativo in ['1', '0']:
            qs = qs.filter(is_active=(ativo == '1'))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categorias'] = Category.objects.all()
        ctx['marcas'] = Brand.objects.all()
        ctx['q'] = self.request.GET.get('q', '')
        ctx['f_categoria'] = self.request.GET.get('categoria', '')
        ctx['f_marca'] = self.request.GET.get('marca', '')
        ctx['f_ativo'] = self.request.GET.get('ativo', '')
        return ctx


class ProductAdminCreateView(StaffRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'painel/produtos/form.html'
    success_url = reverse_lazy('painel:produtos_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['images_formset'] = ProductImageInlineFormSet(self.request.POST, self.request.FILES)
        else:
            ctx['images_formset'] = ProductImageInlineFormSet()
        ctx['action'] = 'create'
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        images_formset = ProductImageInlineFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if images_formset.is_valid():
            images_formset.save()
        return response


class ProductAdminUpdateView(StaffRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'painel/produtos/form.html'
    success_url = reverse_lazy('painel:produtos_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['images_formset'] = ProductImageInlineFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            ctx['images_formset'] = ProductImageInlineFormSet(instance=self.object)
        ctx['action'] = 'update'
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        images_formset = ProductImageInlineFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if images_formset.is_valid():
            images_formset.save()
        return response


class ProductAdminDeleteView(StaffRequiredMixin, DeleteView):
    model = Product
    template_name = 'painel/produtos/confirm_delete.html'
    success_url = reverse_lazy('painel:produtos_list')


class ProductToggleActiveView(StaffRequiredMixin, View):
    def post(self, request, pk):
        produto = Product.objects.get(pk=pk)
        produto.is_active = not produto.is_active
        produto.save(update_fields=['is_active'])
        return redirect('painel:produtos_list')


class ProductToggleFeaturedView(StaffRequiredMixin, View):
    def post(self, request, pk):
        produto = Product.objects.get(pk=pk)
        produto.is_featured = not produto.is_featured
        produto.save(update_fields=['is_featured'])
        return redirect('painel:produtos_list')


class ProductAdjustStockView(StaffRequiredMixin, View):
    def post(self, request, pk):
        try:
            delta = int(request.POST.get('delta', '0'))
        except ValueError:
            return HttpResponseForbidden('Parâmetro inválido')
        produto = Product.objects.get(pk=pk)
        new_qty = max(0, produto.stock_quantity + delta)
        produto.stock_quantity = new_qty
        produto.save(update_fields=['stock_quantity'])
        return redirect('painel:produtos_list')
