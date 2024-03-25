from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView, UpdateView, CreateView, FormView
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.core.cache import cache
from django.contrib.auth.mixins import PermissionRequiredMixin

from services.check_count_product import CheckCountProduct
from services.check_full_name import check_name
from services.slugify import slugify
from django.core.paginator import Paginator

from .tasks import pay_order
from .configs import settings
from .forms import ReviewsForm, OrderCreateForm, RegisterForm, PaymentForm
from .filters import ProductFilter
from .mixins import ChangeListMixin
from authorization.models import Profile
from cart.cart import Cart
from cart.models import Cart as Basket
from .models import Product, Orders, Offer, BannersCategory, Discount
from services.services import (ProductService,
                               CatalogService,
                               CategoryServices,
                               GetParamService,
                               ProductsViewService,
                               ReviewsProduct,
                               MainService,
                               )

import logging
import re
from typing import Any


class CatalogListView(ListView):
    """
    Вьюшка каталога
    """

    template_name = 'store/catalog/catalog.html'
    model = Product
    context_object_name = 'products'
    paginate_by = 8

    def get_queryset(self) -> Product.objects:
        """
        Функция возвращает отфильтрованные продукты по категории, тегу, фильтру или сортировке.
        Если переданные GET параметры совпадают с кэшированными, то продукты берутся из кэша.
        """

        queryset = super().get_queryset()
        get_params_for_queryset = cache.get('get_params')
        category = self.request.resolver_match.captured_kwargs.get('slug')

        if category:
            queryset = CategoryServices.product_by_category(
                self.request.resolver_match.captured_kwargs['slug']
            )

        if self.request.GET and get_params_for_queryset == self.request.GET and not category:
            self.filtered_and_sorted = cache.get('products')
        else:
            product_filter = ProductFilter(self.request.GET, queryset=queryset)
            self.filtered_and_sorted = CatalogService().catalog_processing(self.request, product_filter)

            cache.set('get_params', self.request.GET, settings.get_cache_filter_params())
            cache.set('products', self.filtered_and_sorted, settings.get_cache_catalog())

        return self.filtered_and_sorted.qs

    def get_context_data(self, **kwargs) -> HttpResponse:
        """
        Функция возвращает контекст
        """

        context = super().get_context_data(**kwargs)

        context['filter'] = self.filtered_and_sorted.form
        context['tags'] = CatalogService.get_popular_tags()
        context['full_path'] = GetParamService(self.request.get_full_path()).remove_param('sorting').get_url()

        return context


class ProductDetailView(DetailView):
    """
    Вьюшка детальной страницы товара
    """

    template_name = 'store/product/product-detail.html'
    model = Product
    context_object_name = 'product'

    def get_object(self, *args, **kwargs) -> Product.objects:
        slug = self.kwargs.get('slug')
        instance = Product.objects.get(slug=slug)
        product = cache.get_or_set(f'product-{slug}', instance, settings.get_cache_product_detail())

        ProductsViewService(self.request).add_product_to_viewed(product.id)

        return product

    def get_context_data(self, **kwargs) -> HttpResponse:
        context = super().get_context_data(**kwargs)

        context['num_reviews'] = ReviewsProduct.get_number_of_reviews_for_product(self.object)
        context['reviews_num3'], context['reviews_all'] = ReviewsProduct.get_list_of_product_reviews(self.object)
        context['form'] = ReviewsForm()
        context.update({'toast_message': cache.get('toast_message')})
        context.update(ProductService(context['product']).get_context())

        return context

    def post(self, request, *args, **kwargs):
        form = ReviewsForm(request.POST)
        if form.is_valid():
            ReviewsProduct.add_review_to_product(request, form, self.kwargs['slug'])

        numbers = request.POST.get('amount')
        if numbers:
            cart = Cart(request)
            product = get_object_or_404(Product, slug=kwargs['slug'])
            offer = get_object_or_404(Offer, id=product.offers.first().id)
            cart.add_product(offer, quantity=int(numbers))

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class SettingsView(PermissionRequiredMixin, ChangeListMixin, ListView):
    """
    Класс SettingsView отображает страницу с настройками
    """

    model = Product
    template_name = 'admin/settings.html'
    permission_required = 'authorization.view_storesettings'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        change_list = self.get_change_list_admin(title="Settings")

        return dict(list(context.items()) + list(change_list.items()))


class ClearCacheAll(ChangeListMixin, TemplateView):
    """
    Класс ClearCacheAll позволяет очистить весь кэш сайта
    """

    template_name = 'admin/settings.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        cache.clear()
        messages.success(self.request, _('кэш полностью очищен.'))  # Добавление сообщения для действия

        return context

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        if cache:
            super().dispatch(request, *args, **kwargs)

        return HttpResponseRedirect(reverse_lazy("store:settings"))


class ClearCacheBanner(ChangeListMixin, TemplateView):
    """
    Класс ClearCacheBanner позволяет очистить кэш Баннера
    """

    template_name = 'admin/settings.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        cache.delete("banners")
        messages.success(self.request, _('кэш баннера очищен.'))

        return context

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        if cache:
            super().dispatch(request, *args, **kwargs)

        return HttpResponseRedirect(reverse_lazy("store:settings"))


class ClearCacheCart(ChangeListMixin, TemplateView):
    """
    Класс ClearCacheCart позволяет очистить кэш Корзины
    """

    template_name = 'admin/settings.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        cache.delete("cart")
        messages.success(self.request, _('кэш корзины очищен.'))

        return context

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        if cache:
            super().dispatch(request, *args, **kwargs)

        return HttpResponseRedirect(reverse_lazy("store:settings"))


class ClearCacheProductDetail(ChangeListMixin, TemplateView):
    """
    Класс ClearCacheProductDetail позволяет очистить кэш детализации продуктов
    """

    template_name = 'admin/settings.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        cache.delete("product_detail")
        messages.success(self.request, _('кэш продукта очищен.'))

        return context

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        if cache:
            super().dispatch(request, *args, **kwargs)
        return HttpResponseRedirect(reverse_lazy("store:settings"))


class ClearCacheSeller(ChangeListMixin, TemplateView):
    """
    Класс ClearCacheProductDetail позволяет очистить кэш детализации продуктов
    """

    template_name = 'admin/settings.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        cache.delete("seller")
        messages.success(self.request, _('кэш продавца очищен.'))

        return context

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        if cache:
            super().dispatch(request, *args, **kwargs)

        return HttpResponseRedirect(reverse_lazy("store:settings"))


class ClearCacheCatalog(ChangeListMixin, TemplateView):
    """
    Класс ClearCacheCatalog позволяет очистить кэш детализации продуктов и параметров фильтра
    """

    template_name = 'admin/settings.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        cache.delete("get_params")
        cache.delete("products")
        messages.success(self.request, _('кэш каталога очищен.'))

        return context

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        if cache:
            super().dispatch(request, *args, **kwargs)

        return HttpResponseRedirect(reverse_lazy("store:settings"))


class SiteName(ChangeListMixin, TemplateView):
    """
    Класс SiteName позволяет задать новое название интернет магазина
    """

    template_name = 'admin/settings.html'

    def post(self, request) -> HttpResponse:
        title_site = request.POST.get('title_site')
        if title_site:
            settings.set_site_name(title_site)
            messages.success(self.request, _('Название магазина успешно изменено'))
        else:
            messages.warning(self.request, _('Поле не должно быть пустым'))

        return HttpResponseRedirect(reverse_lazy('store:settings'))


class CacheSetupBannerView(ChangeListMixin, TemplateView):
    """
    Класс CacheSetupBannerView позволяет задать или обновить время кэширования Баннера
    """

    template_name = 'admin/settings.html'

    def post(self, request) -> HttpResponse:
        cache_time_banner = request.POST.get('cache_time_banner')
        time_banner = re.findall(r'[0-9]+', cache_time_banner)
        if time_banner:
            settings.set_cache_banner(time_banner[0])
            messages.success(self.request, _('Время кэширование Баннера установлено'))
        else:
            messages.warning(self.request, _('Поле не должно быть пустым или содержать только цифры'))

        return HttpResponseRedirect(reverse_lazy('store:settings'))


class CacheSetupCartView(ChangeListMixin, TemplateView):
    """
    Класс CacheSetupCartView позволяет задать или обновить время кэширования Корзины
    """

    template_name = 'admin/settings.html'

    def post(self, request) -> HttpResponse:
        cache_time_cart = request.POST.get('cache_time_cart')
        time_cart = re.findall(r'[0-9]+', cache_time_cart)
        if time_cart:
            settings.set_cache_cart(time_cart[0])
            messages.success(self.request, _('Время кэширование Корзины установлено'))
        else:
            messages.warning(self.request, _('Поле не должно быть пустым или содержать только цифры'))

        return HttpResponseRedirect(reverse_lazy('store:settings'))


class CacheSetupProdDetailView(ChangeListMixin, TemplateView):
    """
    Класс CacheSetupProdDetailView позволяет задать или обновить время кэширования детальной информации продукта
    """

    template_name = 'admin/settings.html'

    def post(self, request) -> HttpResponse:
        cache_time_prod_detail = request.POST.get('cache_time_prod_detail')
        time_prod_detail = re.findall(r'[0-9]+', cache_time_prod_detail)
        if time_prod_detail:
            settings.set_cache_product_detail(time_prod_detail[0])
            messages.success(self.request, _('Время кэширование детализации продукта установлено'))
        else:
            messages.warning(self.request, _('Поле не должно быть пустым или содержать только цифры'))

        return HttpResponseRedirect(reverse_lazy('store:settings'))


class CacheSetupSellerView(ChangeListMixin, TemplateView):
    """
    Класс CacheSetupSellerView позволяет задать или обновить время кэширования детальной информации продавца
    """

    template_name = 'admin/settings.html'

    def post(self, request) -> HttpResponse:
        cache_time_seller = request.POST.get('cache_time_seller')
        time_seller = re.findall(r'[0-9]+', cache_time_seller)
        if time_seller:
            settings.set_cache_seller(time_seller[0])
            messages.success(self.request, _('Время кэширование детализации продавца установлено'))
        else:
            messages.warning(self.request, _('Поле не должно быть пустым или содержать только цифры'))

        return HttpResponseRedirect(reverse_lazy('store:settings'))


class CacheSetupCatalogView(ChangeListMixin, TemplateView):
    """
    Класс CacheSetupCatalogView позволяет задать или обновить время кэширования каталога
    """

    template_name = 'admin/settings.html'

    def post(self, request) -> HttpResponse:
        cache_time_catalog = request.POST.get('cache_time_catalog')
        time_catalog = re.findall(r'[0-9]+', cache_time_catalog)
        if time_catalog:
            settings.set_cache_catalog(time_catalog[0])
            messages.success(self.request, _('Время кэширование детализации продавца установлено'))
        else:
            messages.warning(self.request, _('Поле не должно быть пустым или содержать только цифры'))

        return HttpResponseRedirect(reverse_lazy('store:settings'))


class MainPage(ListView):
    """
    Главная страница
    """

    template_name = 'store/index.html'
    model = Product

    def get_queryset(self):
        """
        Queryset:
            'pk': int,
            'preview': image url,
            'name': str,
            'category__name': str,
            'offer__unit_price': Decimal,
            'count': int
        """

        cache_key = 'product_list_cache'
        popular_products = cache.get(cache_key)

        if popular_products is None:
            try:
                popular_products = ProductService(self.model).get_popular_products(quantity=6)

            except Exception as exception:
                popular_products = None
                logging.error(exception)

        cache.set(cache_key, popular_products, settings.set_popular_products_cache(1))

        return popular_products

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['banners_category'] = BannersCategory.objects.all()[:3]
        context['limited_deals'] = MainService.get_limited_deals()
        context['hot_offers'] = Product.objects.all().filter(discount__is_active=True).distinct('pk')[:9]
        context['limited_edition'] = Product.objects.filter(limited_edition=True).distinct('pk')[:16]

        return context


class OrderRegisterView(CreateView):
    """
    Класс регистрации пользователя.
    После регистрации пользователь авторизуется.
    """

    template_name = 'store/order/order_register.html'
    form_class = RegisterForm

    def form_valid(self, form):
        user = form.save()
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        phone = form.cleaned_data.get('phone')
        Profile.objects.create(
            user=user,
            slug=slugify(username),
            phone=phone,
        )
        user = authenticate(username=username, password=password)
        login(self.request, user)

        return redirect(reverse_lazy("store:order_create", kwargs={'pk': user.pk}))


class OrderView(UpdateView):
    """
    Класс позволяет оформить заказ для пользователя и очистить корзину из сессии.
    Перед оформлением заказа товар проверяется:
    1. Проверка на отсутствие товара.
    2. Проверка на кол-во заказанного товара больше, чем доступно в магазине.
    """

    model = User
    template_name = 'store/order/order_create.html'
    form_class = OrderCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'form': self.get_data
            }
        )

        return context

    def get_data(self):
        user = self.request.user
        profile = Profile.objects.get(user=user)
        address = profile.address.split(' ')
        data = {
            'name': user.first_name + ' ' + user.last_name,
            'email': user.email,
            'phone': profile.phone,
            'city': address[0],
            'address': ' '.join(address[1:])
        }
        form = OrderCreateForm(data)

        return form

    def form_valid(self, form):
        cart = Cart(self.request)
        user = form.save(commit=False)
        profile = Profile.objects.get(user=user)
        user.first_name, user.last_name = check_name(form.cleaned_data['name'])
        delivery = form.cleaned_data['delivery']
        payment = form.cleaned_data['payment']
        user.email = form.cleaned_data['email']
        user.save()

        profile.phone = form.cleaned_data['phone']
        profile.address = f"{form.cleaned_data['city']} {form.cleaned_data['address']}"
        profile.save()

        order = Orders.objects.create(
            delivery_type=delivery,
            payment=payment,
            profile=profile,
            address=profile.address,
            total_payment=sum([item['total_price'] for item in cart]),
            status=3,
        )
        order.save()

        for item in cart:
            order.products.add(item['product'])
            Basket.objects.create(
                order=order,
                products=item['product'],
                quantity=item['quantity'],
            )

            CheckCountProduct(item['offer_id']).calculating_amount_of_basket(item, item['offer_id'])

        cart.clear()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('store:order_confirm', kwargs={'pk': self.request.user.profile.orders.last().id})


class OrderConfirmView(TemplateView):
    """
    Подтверждение заказа и переход на страницу оплаты
    """

    model = Orders
    template_name = 'store/order/order_confirm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'order': Orders.objects.get(id=self.kwargs['pk']),
            }
        )

        return context

    def get_success_url(self):
        return reverse_lazy('store:order_confirm', kwargs={'pk': self.kwargs['pk']})


class DiscountList(ListView):
    """
    Представление для просмотра страницы скидок
    """

    model = Discount
    template_name = 'store/discount/discount_list.html'

    def get_context_data(self, **kwargs):
        """
        Функция возвращает контекст
        """
        context = super().get_context_data(**kwargs)
        context['page_obj'] = (Paginator(Discount.objects.filter(is_active=True), 12)
                               .get_page(self.request.GET.get('page')))

        return context


class DiscountDetail(DetailView):
    """
    Представление для просмотра детальной страницы скидок
    """

    model = Discount
    template_name = 'store/discount/discount_details.html'

    def get_context_data(self, **kwargs):
        """
        Функция возвращает контекст
        """
        context = super().get_context_data(**kwargs)
        context['discount'] = Discount.objects.get(slug=self.kwargs['slug'])

        return context


class PaymentFormView(FormView):
    """
    Вьюшка формы оплаты
    """

    template_name = 'store/order/payment.html'
    form_class = PaymentForm

    def form_valid(self, form: PaymentForm) -> HttpResponse:
        """
        Отправляет оплату в очередь, если форма прошла валидацию
        """

        Orders.objects.filter(id=self.kwargs['pk']).update(status=3)

        pay_order.apply_async(
            kwargs={
                'order_id': self.kwargs['pk'],
                'card': form.cleaned_data['bill']
            },
            countdown=10,
            queue='payment',
        )

        return redirect(reverse_lazy('store:payment-progress', kwargs={'pk': self.kwargs['pk']}))

    def get_context_data(self, **kwargs) -> dict:
        """
        Передает в контекст тип оплаты по id заказа
        """

        order_n = _('Заказ с номером')
        not_found = _('не найден')

        context = super().get_context_data(**kwargs)
        try:
            order_status = Orders.objects.get(id=self.kwargs['pk']).status
            if order_status == 1:
                context.update(
                    {
                        'order_paid': True,
                    }
                )
            else:
                payment_type = Orders.objects.get(id=self.kwargs['pk']).payment
                context.update(
                    {
                        'payment_type': payment_type,
                    }
                )

            return context

        except ObjectDoesNotExist:
            context.update(
                {
                    'error': f'{order_n} {self.kwargs["pk"]} {not_found}',
                }
            )
            return context


class PaymentProgressView(TemplateView):
    """
    Вьюшка страницы ожидания оплаты
    """

    template_name = 'store/order/payment_progress.html'

    def get(self, *args, **kwargs) -> HttpResponse:
        """
        Проверяет статус оплаты, если изменился - отправляет на детальную страницу заказа
        """

        try:
            status = Orders.objects.get(id=self.kwargs['pk']).status
            if status != 3:
                return redirect(reverse_lazy(
                    'profile:detailed_order',
                    kwargs={
                        'slug': self.request.user.profile.slug,
                        'pk': self.kwargs['pk']
                    }
                ))

            return super().get(self.request, *args, **kwargs)

        except ObjectDoesNotExist:
            return redirect(reverse_lazy('store:index'))
