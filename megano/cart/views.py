from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

from services.services import DiscountProduct
from .cart import Cart
from store.models import Product, Offer

from typing import Any


class CartListView(TemplateView):
    template_name = 'store/cart.html'

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        discount = DiscountProduct()
        context.update(
            {
                'carts': Cart(self.request),
                'offers': Offer.objects.all(),
                'total_price': discount.get_priority_discount(cart=Cart(self.request))
            }
        )
        return context

    def post(self, request) -> HttpResponseRedirect:
        offer = Offer.objects.get(id=request.POST.get('offer'))
        carts = Cart(request)
        for item in carts:
            if item['product'].id == offer.product.id:
                carts.update_date(offer, offer.unit_price)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class AddProductToCartView(TemplateView):
    """
    Добавление товара в корзину
    """

    template_name = 'store/cart.html'

    def get(self, request, *args, **kwargs) -> HttpResponseRedirect:
        cart = Cart(request)
        offer = get_object_or_404(Offer, id=kwargs['offer_id'])
        cart.add_product(offer, update=False)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class AddProductView(TemplateView):
    """
    Добавить одну единицу товара в корзине (+1шт.)
    """

    template_name = 'store/cart.html'

    def get(self, request, *args, **kwargs) -> HttpResponseRedirect:
        cart = Cart(request)
        product = get_object_or_404(Product, slug=kwargs['slug'])
        cart_add = int(cart.cart[f'{product.id}']['offer_id'])
        cart.add(get_object_or_404(Offer, id=cart_add))
        return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))


class TakeProductView(TemplateView):
    """
    Убрать одну единицу товара в корзине (-1шт.)
    """

    template_name = 'store/cart.html'

    def get(self, request, *args, **kwargs) -> HttpResponseRedirect:
        cart = Cart(request)
        product = get_object_or_404(Product, slug=kwargs['slug'])
        cart_take = int(cart.cart[f'{product.id}']['offer_id'])
        cart.take(get_object_or_404(Offer, id=cart_take))
        return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))


class DeleteProductFromCartView(TemplateView):
    """
    Удаление продукта из корзины
    """

    template_name = 'store/cart.html'

    def get(self, request, *args, **kwargs) -> HttpResponseRedirect:
        cart = Cart(request)
        cart.remove(get_object_or_404(Product, slug=kwargs['slug']))
        return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))


class ClearCartView(TemplateView):
    """
    Очистка корзины от всех продуктов
    """

    template_name = 'store/cart.html'

    def get(self, request, *args, **kwargs) -> HttpResponseRedirect:
        cart = Cart(request)
        cart.clear()
        return redirect('cart:index')
