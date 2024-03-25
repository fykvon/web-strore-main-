from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from compare.services import (get_comparison_list,
                              _add_product_to_comparison,
                              get_compare_info,
                              )
from store.models import Product


class AddToComparisonView(View):
    """
    Контроллер добавления товаров к сравнению
    """

    def get(self, request, *args, **kwargs):
        product_id = self.kwargs.get('product_id')
        product = get_object_or_404(Product, id=product_id)

        # Создаем уникальный comparison_id
        comparison_id = product.get_comparison_id()
        # сервис по добавлению товара к сравнению
        _add_product_to_comparison(request, comparison_id)

        return redirect(request.META.get('HTTP_REFERER'))


class ClearComparisonView(View):
    """
    Контроллер для очистки страницы сравнения
    """

    def get(self, request, *args, **kwargs):

        if request.user.is_authenticated:
            # Если пользователь авторизован, очищаем сессию
            request.session['comparison_list'] = []
        else:
            # Если пользователь не авторизован, очищаем куки
            response = redirect('store:catalog')
            response.delete_cookie('comparison_list')
            return response

        return redirect('compare:comparison')


class ComparisonView(View):
    """
    Контроллер сравнения товаров
    """

    template_name = 'compare/compare_products.html'

    def get(self, request, *args, **kwargs):
        try:
            if request.user.is_authenticated:
                # Если пользователь авторизован, используем сессии
                comparison_list = request.session.get('comparison_list', [])
            else:
                # Если пользователь не авторизован, используем куки
                comparison_list = request.COOKIES.get('comparison_list', '').split(',')
            if len(comparison_list) == 0:
                return redirect(reverse_lazy("compare:comparison_none"))
            products = get_comparison_list(comparison_list)
            result = get_compare_info(products)
            return render(request, self.template_name, context={'product_characteristic_list': result})
        except:
            return redirect(reverse_lazy("compare:comparison_error"))


class ComparisonErrorView(TemplateView):
    """
    Контроллер происходит при ошибке сравнения товаров
    """

    template_name = 'compare/compare_error.html'

    def get(self, request, *args, **kwargs):
        message = _('Нельзя сравнивать несравнимое. Выберите товары из одной категории. Добавь товары снова')
        if request.user.is_authenticated:
            # Если пользователь авторизован, используем сессии
            comparison_list = request.session.get('comparison_list', [])
        else:
            # Если пользователь не авторизован, используем куки
            comparison_list = request.COOKIES.get('comparison_list', '').split(',')
        comparison_list.clear()

        return render(request, self.template_name, context={'message': message})


class ComparisonNoneView(TemplateView):
    """
    Контроллер если нечего сравнивать
    """

    template_name = 'compare/compare_none.html'

    def get(self, request, *args, **kwargs):
        message = _('Тут пока ничего нет. Добавь товары к сравнению')
        return render(request, self.template_name, context={'message': message})
