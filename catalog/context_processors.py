from .models import Cart


def cart(request):
    """Context processor para incluir el carrito en todos los templates"""
    cart = None
    cart_items = []
    cart_total = 0
    cart_items_count = 0

    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if request.session.session_key:
            cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)

    if cart:
        cart_items = cart.items.all()
        cart_total = cart.total_with_iva
        cart_items_count = cart.total_items

    return {
        'cart': cart,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_items_count': cart_items_count,
    }











