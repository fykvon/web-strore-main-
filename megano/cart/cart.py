import copy
from decimal import Decimal
from django.conf import settings

from store.models import Product, Offer
from services.check_count_product import CheckCountProduct

MAX_COUNT = 21


class Cart(object):
    """
    Класс корзины для хранения, добавления, удаления товаров.
    """

    def __init__(self, request) -> None:
        self.session = request.session
        cart = self.session.get(settings.CART_ID)
        if not cart:
            cart = self.session[settings.CART_ID] = {}
        self.cart = cart

    def __check_product_to_cart(self, product: Product):
        product_id = str(product.id)
        if product_id in self.cart:
            return product_id

    def add_product(self, offer, quantity: int = 1, update: bool = False) -> None:
        """
        Метод добавления товара в корзину на странице сайта
        """

        if CheckCountProduct(offer=offer.id).checking_product_for_zero(quantity):
            product_id = str(offer.product.id)
            if product_id not in self.cart:
                self.cart[product_id] = {'quantity': 0, 'price': str(offer.unit_price),
                                         'offer_id': str(offer.id), 'offer_name': str(offer.seller.name_store),
                                         'd_price': str(offer.get_discount_price())}
            if update:
                self.cart[product_id]['quantity'] = quantity
            else:
                self.cart[product_id]['quantity'] += quantity
            self.save()

    def add(self, offer: Offer, quantity: int = 1) -> None:
        """
        Добавление кол-ва товара на странице корзины (+1 шт.)
        """

        product_id = self.__check_product_to_cart(offer.product)
        if CheckCountProduct(offer=offer.id).check_more_than_it_is(self.cart[product_id]):
            if 1 <= self.cart[product_id]['quantity'] < MAX_COUNT:
                self.cart[product_id]['quantity'] += quantity
            self.save()

    def take(self, offer: Offer, quantity: int = 1) -> None:
        """
        Удаление кол-ва товара на странице корзины (-1 шт.)
        """

        product_id = self.__check_product_to_cart(offer.product)
        if 1 < self.cart[product_id]['quantity'] <= MAX_COUNT:
            self.cart[product_id]['quantity'] -= quantity
        self.save()

    def save(self) -> None:
        """
        Сохранение объекта
        """

        self.session.modified = True

    def remove(self, product: Product) -> None:
        """
        Удаление товара из корзины
        """

        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __len__(self) -> int:
        """
        Общее кол-во товаров сохраненных в корзине

        :return: int
        """

        return sum(item['quantity'] for item in self.cart.values())

    def __iter__(self):
        """
        Итератор для перебора товаров в корзине
        """

        product_id = self.cart.keys()
        products = Product.objects.filter(id__in=product_id)

        cart = copy.deepcopy(self.cart)
        for product in products:
            cart[str(product.id)]['product'] = product
        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']

            yield item

    def get_total_price(self) -> [int, float]:
        """
        Возвращает общую стоимость всей корзины
        """

        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )

    def update_date(self, offer: Offer, price: int) -> None:
        product_id = str(offer.product.id)
        self.cart[product_id]['price'] = str(price)
        self.cart[product_id]['offer_id'] = str(offer.id)
        self.cart[product_id]['offer_name'] = str(offer.seller.name_store)
        self.save()

    def clear(self) -> None:
        """
        Очищает всю корзину
        """

        del self.session[settings.CART_ID]
        self.save()
