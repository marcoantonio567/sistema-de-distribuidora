from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, TemplateView, DetailView
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.db import transaction
from .models import Order, OrderItem, ShippingAddress
from cart.models import Cart
from cart.views import CartMixin
from products.models import Product
import logging

logger = logging.getLogger('orders')


class CheckoutView(CartMixin, TemplateView):
    """View for checkout process"""
    template_name = 'orders/checkout.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.get_cart(self.request)
        
        # Check if cart is valid for checkout
        if not cart.is_valid_for_checkout():
            messages.error(self.request, 'Seu carrinho está vazio ou contém produtos indisponíveis.')
            return redirect('cart:cart_detail')
        
        context['cart'] = cart
        context['cart_items'] = cart.items.select_related('product').all()
        context['total_amount'] = cart.total_amount
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Process checkout form"""
        try:
            cart = self.get_cart(request)
            
            # Validate cart
            if not cart.is_valid_for_checkout():
                messages.error(request, 'Seu carrinho está vazio ou contém produtos indisponíveis.')
                return redirect('cart:cart_detail')
            
            # Get form data
            customer_name = request.POST.get('customer_name', '').strip()
            customer_email = request.POST.get('customer_email', '').strip()
            customer_phone = request.POST.get('customer_phone', '').strip()
            
            # Shipping address
            street = request.POST.get('street', '').strip()
            number = request.POST.get('number', '').strip()
            complement = request.POST.get('complement', '').strip()
            neighborhood = request.POST.get('neighborhood', '').strip()
            city = request.POST.get('city', '').strip()
            state = request.POST.get('state', '').strip()
            zip_code = request.POST.get('zip_code', '').strip()
            reference = request.POST.get('reference', '').strip()
            
            # Validate required fields
            required_fields = {
                'Nome': customer_name,
                'Email': customer_email,
                'Telefone': customer_phone,
                'Rua': street,
                'Número': number,
                'Bairro': neighborhood,
                'Cidade': city,
                'Estado': state,
                'CEP': zip_code,
            }
            
            missing_fields = [field for field, value in required_fields.items() if not value]
            if missing_fields:
                messages.error(request, f'Por favor, preencha os campos obrigatórios: {", ".join(missing_fields)}')
                return self.render_to_response(self.get_context_data())
            
            # Validate email format
            if '@' not in customer_email or '.' not in customer_email.split('@')[-1]:
                messages.error(request, 'Por favor, insira um email válido.')
                return self.render_to_response(self.get_context_data())
            
            # Create order with transaction
            with transaction.atomic():
                # Create order
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    session_key=request.session.session_key,
                    customer_name=customer_name,
                    customer_email=customer_email,
                    customer_phone=customer_phone,
                    subtotal=cart.total_amount,
                    total_amount=cart.total_amount,  # Add shipping calculation here if needed
                )
                
                # Create shipping address
                ShippingAddress.objects.create(
                    order=order,
                    street=street,
                    number=number,
                    complement=complement,
                    neighborhood=neighborhood,
                    city=city,
                    state=state,
                    zip_code=zip_code,
                    reference=reference,
                )
                
                # Create order items and update stock
                for cart_item in cart.items.all():
                    # Check stock again (in case it changed)
                    if not cart_item.product.is_in_stock or cart_item.product.stock_quantity < cart_item.quantity:
                        raise ValueError(f"Produto {cart_item.product.name} está fora de estoque.")
                    
                    # Create order item
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.price,
                        subtotal=cart_item.subtotal,
                    )
                    
                    # Update product stock
                    cart_item.product.decrease_stock(cart_item.quantity)
                
                # Clear cart
                cart.clear()
            
            # Send order confirmation email
            self.send_order_confirmation(order)
            
            logger.info(f"Order {order.order_number} created successfully")
            messages.success(request, f'Pedido {order.order_number} criado com sucesso!')
            
            return redirect('orders:order_success', order_number=order.order_number)
            
        except ValueError as e:
            messages.error(request, str(e))
            return self.render_to_response(self.get_context_data())
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            messages.error(request, 'Erro ao processar pedido. Por favor, tente novamente.')
            return self.render_to_response(self.get_context_data())
    
    def send_order_confirmation(self, order):
        """Send order confirmation email"""
        try:
            subject = f'Confirmação de Pedido - {order.order_number}'
            html_message = render_to_string('orders/order_confirmation_email.html', {'order': order})
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.customer_email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Order confirmation email sent for order {order.order_number}")
        except Exception as e:
            logger.error(f"Error sending order confirmation email: {e}")


class OrderSuccessView(DetailView):
    """View for successful order placement"""
    model = Order
    template_name = 'orders/order_success.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'
    
    def get_queryset(self):
        return Order.objects.select_related('shipping_address').prefetch_related('items__product')


class OrderDetailView(DetailView):
    """View for order details"""
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'
    
    def get_queryset(self):
        return Order.objects.select_related('shipping_address').prefetch_related('items__product', 'status_history')


class OrderListView(TemplateView):
    """View for listing user orders"""
    template_name = 'orders/order_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_authenticated:
            orders = Order.objects.filter(user=self.request.user).order_by('-created_at')
        else:
            # For guest users, show orders from current session
            orders = Order.objects.filter(
                session_key=self.request.session.session_key
            ).order_by('-created_at')
        
        context['orders'] = orders.select_related('shipping_address').prefetch_related('items__product')
        return context


@method_decorator(csrf_exempt, name='dispatch')
class CancelOrderView(View):
    """View to cancel an order"""
    
    def post(self, request, order_number, *args, **kwargs):
        try:
            order = get_object_or_404(Order, order_number=order_number)
            
            # Check if order can be cancelled
            if not order.can_be_cancelled():
                return JsonResponse({
                    'success': False,
                    'error': 'Este pedido não pode ser cancelado.'
                })
            
            # Check if user has permission to cancel
            if request.user.is_authenticated:
                if order.user != request.user:
                    return JsonResponse({
                        'success': False,
                        'error': 'Você não tem permissão para cancelar este pedido.'
                    })
            else:
                if order.session_key != request.session.session_key:
                    return JsonResponse({
                        'success': False,
                        'error': 'Você não tem permissão para cancelar este pedido.'
                    })
            
            # Cancel order and restore stock
            with transaction.atomic():
                # Restore product stock
                for item in order.items.all():
                    item.product.increase_stock(item.quantity)
                
                # Update order status
                order.update_status('cancelled', 'Pedido cancelado pelo cliente')
            
            logger.info(f"Order {order.order_number} cancelled")
            
            return JsonResponse({
                'success': True,
                'message': 'Pedido cancelado com sucesso!',
                'new_status': order.status_display
            })
            
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Erro ao cancelar pedido.'
            })