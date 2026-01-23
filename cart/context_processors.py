from .models import Cart


def cart(request):
    """Context processor to make cart data available in all templates"""
    session_key = request.session.session_key
    
    if not session_key:
        return {'cart': None, 'cart_total': 0, 'cart_amount': 0}
    
    try:
        cart = Cart.objects.get(session_key=session_key)
        return {
            'cart': cart,
            'cart_total': cart.total_items,
            'cart_amount': cart.total_amount
        }
    except Cart.DoesNotExist:
        return {'cart': None, 'cart_total': 0, 'cart_amount': 0}