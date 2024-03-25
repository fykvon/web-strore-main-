from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import Cart


class CartAdmin(admin.ModelAdmin):
    """
    Регистрация модели корзины в админ панели.
    """

    list_display = ['order', 'product_name', 'quantity', 'icon_image', 'created_at', 'updated_at']
    list_filter = ['created_at', 'products']
    search_fields = ['order', 'products']
    list_editable = ['quantity', ]
    list_per_page = 20
    readonly_fields = ['created_at', 'updated_at']

    def product_name(self, obj: Cart) -> str:
        """
        Возвращает укороченное название товара.
        Если название товара больше 20 символов,
        возвращает строку в виде <название...>.
        """

        if len(obj.products.name) > 20:
            return f"{obj.products.name[:20]}..."

        return f"{obj.products.name}"

    def icon_image(self, obj: Cart) -> str:
        """
        Возвращает ссылку на изображение товара в виде иконки.
        """

        return mark_safe(f"<img src='{obj.products.preview.url}' width=50>")

    product_name.short_description = _('Товары')
    icon_image.short_description = _('Иконка')


admin.site.register(Cart, CartAdmin)
