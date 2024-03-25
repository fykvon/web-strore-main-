from .cart import Cart
from services.services import DiscountProduct


def cart(request) -> dict:
    """
    Контекстный процессор позволяет воспользоваться переменной "cart" в любом шаблоне сайта
    """

    cart = Cart(request)

    return {'cart': cart,
            'total_price': DiscountProduct().get_priority_discount(cart)}
