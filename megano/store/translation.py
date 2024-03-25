from modeltranslation.translator import register, TranslationOptions
from .models import Category, Orders, Discount, Product, Banners


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Orders)
class OrdersTranslationOptions(TranslationOptions):
    fields = ('status_exception',)


@register(Discount)
class DiscountTranslationOptions(TranslationOptions):
    fields = ('title', 'description',)


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)


@register(Banners)
class BannersTranslationOptions(TranslationOptions):
    fields = ('title', 'description',)
