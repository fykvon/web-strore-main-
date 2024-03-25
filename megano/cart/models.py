from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from store.models import Product, Orders


class Cart(models.Model):
    """
    Описание модели Корзины

    Orders  - :model:`store.Orders`\n
    Product - :model:`store.Product`
    """

    ordering = _('Заказ')

    order = models.ForeignKey(Orders, on_delete=models.CASCADE, verbose_name=_('Заказ'))
    products = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name=_('Продукты'))
    quantity = models.IntegerField(default=1, verbose_name=_('Количество'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'), db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Дата изменения'))

    def __str__(self) -> str:
        """
        Возвращает имя пользователя и название продукта в виде:
        username: product_name
        """

        return f'({self.ordering} №_{self.order.id}'

    def get_absolute_url(self) -> str:
        """
        Возвращает путь на детальную страницу товаров корзины.
        """

        return reverse('detail', kwargs={'id': self.id})

    class Meta:
        db_table = 'carts'
        ordering = ['-created_at']
        verbose_name = _('корзину')
        verbose_name_plural = _('корзины')
