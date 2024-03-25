from django.utils.translation import gettext_lazy as _, ngettext
from services.message_toast import ToastMessage
from store.models import Offer, Product


class CheckCountProduct:
    """
    Класс проверки стоимости продукта
    """

    products = _('Товара  доступно')
    more = _('Больше')
    not_in_stock = _('нет на складе')

    def __init__(self, offer):
        self.offer = Offer.objects.get(id=offer)
        self.message = ToastMessage()

    def checking_product_for_zero(self, quantity) -> bool:
        """
        Проверка товара на отсутствие (кол-во на складе = 0).
        Если товар отсутствует, значение поля "availability" меняется на False.
        """

        if self.offer.amount == 0:
            product = Product.objects.get(id=self.offer.id)
            product.availability = False
            product.save()
            self.message.toast_message(_('Ошибка'), _('Товар отсутствует на складе'))
            return False
        else:
            if quantity > self.offer.amount:
                piece = ngettext('{self.offer.amount} шт.', '{self.offer.amount}шт.', self.offer.amount)
                self.message.toast_message(_('Ошибка'), f'{self.products} {piece}')
                return False
        return True

    def check_more_than_it_is(self, item):
        """
        Проверка товара в корзине на попытку заказать больше,
        чем имеется на складе.
        """

        if item['quantity'] >= self.offer.amount:
            piece = ngettext('{self.offer.amount} шт.', '{self.offer.amount}шт.', self.offer.amount)
            self.message.toast_message(_('Ошибка'), f'{self.more} {piece} {self.not_in_stock}')
            return False

        return True

    def calculating_amount_of_basket(self, item, offer):
        """
        Вычисление количества товара в корзине из запасов на складе.
        """

        self.offer = offer
        self.offer = Offer.objects.get(id=offer)
        self.offer.amount -= int(item['quantity'])
        self.offer.save()

        self.checking_product_for_zero(item['quantity'])
