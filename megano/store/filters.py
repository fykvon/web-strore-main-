import django_filters
from django import forms
from django.utils.translation import gettext_lazy as _

from authorization.models import Profile
from services.services import CatalogService
from store.widgets import CustomCheckboxMultiple, CustomRadioSelect


class ProductFilter(django_filters.FilterSet):
    """
    Фильтр продуктов в каталоге
    """

    name_placeholder = _('Название')
    feature_placeholder = _('Характеристика')

    CHOICES = (
        (True, _('Да')),
        (False, _('Нет')),
        (None, _('Не учитывать'))
    )

    name = django_filters.CharFilter(
        label=_('Название'),
        widget=forms.TextInput(attrs={
            'class': 'form-input form-input_full',
            'id': 'title',
            'placeholder': name_placeholder,
            'name': 'title',
        }),
        method=CatalogService().filter_products_by_name,
    )
    range = django_filters.CharFilter(
        label=_('Цена'),
        widget=forms.TextInput(attrs={
            'class': 'range-line',
            'type': 'text',
            'id': 'price',
            'name': 'price',
            'data-type': 'double',
            'data-min': '0',
            'data-max': '1000',
        }),
        method=CatalogService().filter_by_price,
    )
    profile = django_filters.ModelMultipleChoiceFilter(
        label=_('Продавцы'),
        queryset=Profile.objects.filter(role='store'),
        widget=CustomCheckboxMultiple(),
        method=CatalogService().filter_by_stores,
    )
    availability = django_filters.TypedChoiceFilter(
        label=_('Только товары в наличии'),
        choices=CHOICES,
        widget=CustomRadioSelect(),
        method=CatalogService().filter_by_availability,
    )
    delivery_free = django_filters.TypedChoiceFilter(
        label=_('С бесплатной доставкой'),
        choices=CHOICES,
        widget=CustomRadioSelect(),
        method=CatalogService().filter_by_delivery,
    )
    feature = django_filters.CharFilter(
        label=_('Характеристика'),
        widget=forms.TextInput(attrs={
            'class': 'form-input form-input_full',
            'id': 'feature',
            'placeholder': feature_placeholder,
            'name': 'feature',
        }),
        method=CatalogService().filter_by_feature,
    )
