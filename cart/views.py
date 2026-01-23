from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from .models import Cart, CartItem
from products.models import Product
import logging

logger = logging.getLogger('cart')


class CartMixin:
    """Mixin to handle cart operations"""
    
    def get_cart(self, request):
        """Get or create cart for the current session"""
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        cart, created = Cart.objects.get_or_create(session_key=session_key)
        return cart


class CartView(CartMixin, TemplateView):
    """View for displaying cart contents"""
    template_name = 'cart/cart_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.get_cart(self.request)
        
        context['cart'] = cart
        context['cart_items'] = cart.items.select_related('product').all()
        context['total_amount'] = cart.total_amount
        context['total_items'] = cart.total_items
        
        return context


@method_decorator(csrf_exempt, name='dispatch')
class AddToCartView(CartMixin, View):
    """View to add products to cart"""
    
    def post(self, request, *args, **kwargs):
        try:
            product_id = request.POST.get('product_id')
            quantity = int(request.POST.get('quantity', 1))
            
            if not product_id:
                return JsonResponse({'success': False, 'error': 'Product ID is required'})
            
            product = get_object_or_404(Product, id=product_id, is_active=True)
            cart = self.get_cart(request)
            
            success = cart.add_item(product, quantity)
            
            if success:
                logger.info(f"Product {product.name} added to cart {cart.id}")
                return JsonResponse({
                    'success': True,
                    'message': 'Produto adicionado ao carrinho!',
                    'cart_total': cart.total_items,
                    'cart_amount': str(cart.total_amount)
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Produto fora de estoque ou quantidade indisponível.'
                })
        
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Quantidade inválida.'})
        except Exception as e:
            logger.error(f"Error adding product to cart: {e}")
            return JsonResponse({'success': False, 'error': 'Erro ao adicionar produto ao carrinho.'})


@method_decorator(csrf_exempt, name='dispatch')
class RemoveFromCartView(CartMixin, View):
    """View to remove products from cart"""
    
    def post(self, request, *args, **kwargs):
        try:
            product_id = request.POST.get('product_id')
            
            if not product_id:
                return JsonResponse({'success': False, 'error': 'Product ID is required'})
            
            product = get_object_or_404(Product, id=product_id)
            cart = self.get_cart(request)
            
            success = cart.remove_item(product)
            
            if success:
                logger.info(f"Product {product.name} removed from cart {cart.id}")
                return JsonResponse({
                    'success': True,
                    'message': 'Produto removido do carrinho.',
                    'cart_total': cart.total_items,
                    'cart_amount': str(cart.total_amount)
                })
            else:
                return JsonResponse({'success': False, 'error': 'Produto não encontrado no carrinho.'})
        
        except Exception as e:
            logger.error(f"Error removing product from cart: {e}")
            return JsonResponse({'success': False, 'error': 'Erro ao remover produto do carrinho.'})


@method_decorator(csrf_exempt, name='dispatch')
class UpdateCartItemView(CartMixin, View):
    """View to update cart item quantity"""
    
    def post(self, request, *args, **kwargs):
        try:
            product_id = request.POST.get('product_id')
            quantity = int(request.POST.get('quantity', 1))
            
            if not product_id:
                return JsonResponse({'success': False, 'error': 'Product ID is required'})
            
            if quantity < 1:
                return JsonResponse({'success': False, 'error': 'Quantidade deve ser pelo menos 1.'})
            
            product = get_object_or_404(Product, id=product_id)
            cart = self.get_cart(request)
            
            success = cart.update_item_quantity(product, quantity)
            
            if success:
                logger.info(f"Cart item {product.name} quantity updated to {quantity} in cart {cart.id}")
                
                # Get the updated item to calculate subtotal
                item = cart.get_item(product)
                return JsonResponse({
                    'success': True,
                    'message': 'Quantidade atualizada!',
                    'cart_total': cart.total_items,
                    'cart_amount': str(cart.total_amount),
                    'item_subtotal': str(item.subtotal) if item else '0.00'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Quantidade indisponível em estoque.'
                })
        
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Quantidade inválida.'})
        except Exception as e:
            logger.error(f"Error updating cart item: {e}")
            return JsonResponse({'success': False, 'error': 'Erro ao atualizar quantidade.'})


class ClearCartView(CartMixin, View):
    """View to clear all items from cart"""
    
    def post(self, request, *args, **kwargs):
        try:
            cart = self.get_cart(request)
            cart.clear()
            
            logger.info(f"Cart {cart.id} cleared")
            messages.success(request, 'Carrinho limpo com sucesso!')
            
            return redirect('cart:cart_detail')
        
        except Exception as e:
            logger.error(f"Error clearing cart: {e}")
            messages.error(request, 'Erro ao limpar carrinho.')
            return redirect('cart:cart_detail')


def cart_summary(request):
    """AJAX endpoint for cart summary"""
    try:
        cart = CartMixin().get_cart(request)
        
        items_data = []
        for item in cart.items.select_related('product').all()[:3]:  # Show only first 3 items
            main_image = item.product.get_main_image()
            items_data.append({
                'id': item.id,
                'product_name': item.product.name,
                'product_url': item.product.get_absolute_url(),
                'quantity': item.quantity,
                'price': str(item.product.price),
                'subtotal': str(item.subtotal),
                'image_url': main_image.image.url if main_image else None
            })
        
        return JsonResponse({
            'success': True,
            'cart_total': cart.total_items,
            'cart_amount': str(cart.total_amount),
            'items': items_data
        })
    
    except Exception as e:
        logger.error(f"Error getting cart summary: {e}")
        return JsonResponse({'success': False, 'error': 'Erro ao obter resumo do carrinho.'})