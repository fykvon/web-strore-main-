import copy
import json
import os
import shutil

from django.core.files.temp import NamedTemporaryFile
from django.core.files import File
from urllib.request import urlopen
from urllib.error import HTTPError

from compare.models import *

from datetime import datetime, timedelta
from decimal import Decimal
from random import choice
from typing import Dict

from django.core.cache import cache
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate, login
from urllib.parse import urlparse, parse_qs, urlencode

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg, Count, When, Case

from django.db import IntegrityError
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from authorization.forms import RegisterForm, LoginForm
from authorization.models import Profile
from store.models import Product, Offer, Category, Reviews, Discount, ProductImage, Tag
from store.utils import import_logger
from .slugify import slugify
from store.models import Orders


class AuthorizationService:
    """
    Сервис авторизации и регистрации пользователей
    """

    @staticmethod
    def register_new_user(request: HttpRequest, form: RegisterForm) -> bool:
        """
        Регистрирует нового пользователя, если указанного email нет в базе данных
        """

        username = form.cleaned_data["username"]
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]

        email_in_db = User.objects.filter(email=email).first()

        if email_in_db:
            return False
        else:
            user = form.save()
            user.set_password(password)
            user.save()

            Profile.objects.create(
                user=user,
                slug=slugify(username),
            )

            user = authenticate(
                request, username=username, password=password
            )

            login(request=request, user=user)

            return True

    @staticmethod
    def get_login(request: HttpRequest, form: LoginForm):
        """
        Авторизует пользователя по email и password

        :return: возвращает True или str - описание ошибки
        """

        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]

        try:
            user = User.objects.get(email=email)

            user = authenticate(request, username=user.username, password=password)

            if user:
                login(request, user)
                return True

            return _('Пароль и email не совпадают, проверьте ввод или зарегистрируйтесь')

        except User.DoesNotExist:
            return _("Пользователь с таким email не найден")


class GetAdminSettings:
    pass


class AddProductInTrash:
    pass


class DiscountProduct:
    """
    Сервис получения скидок на товары и группы товаров
    """

    def get_priority_discount(self, cart):
        """
        Функция проверяет наличие скидки в корзине

        :param cart: корзина с товарами
        :return: общая стоимость корзины
        """

        discounts = Discount.objects.filter(is_active=True)
        discounts_cart_priority = discounts.filter(name='DC', priority=True)
        discounts_set_priority = discounts.filter(name='DS', priority=True)
        discounts_cart = discounts.filter(name='DC', priority=False)
        discounts_set = discounts.filter(name='DS', priority=False)
        if discounts_cart_priority:
            price = self.get_discount_on_cart(discounts_cart_priority, cart)
            if price:
                return price
        elif discounts_set_priority:
            price = self.get_discount_on_set(discounts_set_priority, cart)
            if price:
                return price
        elif discounts_cart:
            price = self.get_discount_on_cart(discounts_cart, cart)
            if price:
                return price
        elif discounts_set:
            price = self.get_discount_on_set(discounts_set, cart)
            if price:
                return price
        return self.get_discount_on_product(cart)

    @staticmethod
    def calculate_price_with_discount(product, price) -> float:
        """"
       Функция расчитывает стоимость товара со скидкой

       :param product: товар
       :param price: цена продукта
       :return: цена продукта со сидкой
       """

        finish_price = float(
            product['product'].offers.first().unit_price
        )
        finish_price -= finish_price * (price / 100)
        finish_price *= product['quantity']

        return finish_price

    @staticmethod
    def total_price_cart(cart):
        """"
        Функция расчитывает стоимость карзины без скидки 'Скидки на товары'

        :param cart: карзина с товарами
        :return: стоимость карзины без скидок
        """

        cart_product = [crt for crt in cart]
        price = sum([product['price'] * product['quantity'] for product in cart_product])
        return price

    @staticmethod
    def discount_ids(discount):
        """
        Функция для получения списка id товаров в скидке
        """

        discount_products = discount.products.all()
        return [product.id for product in discount_products]

    @staticmethod
    def categories_ids(discount):
        """
        Функция для получения списка id категорий в скидке
        """

        discount_products = discount.categories.all()
        return [category.id for category in discount_products]

    def get_discount_on_cart(self, discounts, cart):
        """
        Функция расчитывает стоимость карзины со скидкой 'Скидки на корзину'

        :param discounts: список скидок 'Скидки на корзину'
        :param cart: карзина с товарами
        :return: стоимость карзины со скидкой 'Скидки на корзину'
        """

        total_products = len(cart)
        total_price = self.total_price_cart(cart)
        for discount in discounts:
            total_discount_products = discount.total_products
            if (total_discount_products == total_products
                    and discount.sum_cart <= total_price):
                if discount.sum_discount >= 1:
                    return discount.sum_discount

    def get_discount_on_set(self, discounts, cart):
        """
        Функция расчитывает стоимость карзины со скидкой 'Скидки на наборы'

        :param discounts: список скидок 'Скидки на наборы'
        :param cart: карзина с товарами
        :return: стоимость карзины со скидкой 'Скидки на наборы'
        """

        cart_id = [crt['product'].id for crt in cart]
        cart_categories_id = [crt['product'].category.id for crt in cart]
        for discount in discounts:
            product_ids = self.discount_ids(discount)
            category_ids = self.categories_ids(discount)
            if (str(product_ids)[1:-1] in str(cart_id)[1:-1]
                    and str(category_ids)[1:-1] in str(cart_categories_id)[1:-1]):
                price = self.total_price_cart(cart)
                price -= Decimal(discount.sum_discount)

                return 1 if price <= 1 else price

    def get_discount_on_product(self, cart):
        """
       Функция расчитывает стоимость карзины со скидкой 'Скидки на товар'

       :param cart: карзина с товарами
       :return: стоимость карзины со скидкой 'Скидки на товар'
       """

        cart_product = [crt for crt in cart]
        price = 0
        for product in cart_product:
            price += round(int(self.get_price_discount_on_product(product)), 2)
        return price

    def get_price_discount_on_product(self, product):
        """
        Функция применяет скидку 'Скидки на товар', если она есть
        """

        products = Product.objects.filter(discount__name='DP',
                                          discount__is_active=True)
        categories = Category.objects.filter(discount__name='DP',
                                             discount__is_active=True)
        if product['product'] in products:
            return self.get_price_product(product)
        elif product['product'].category in categories:
            return self.get_price_categories(product)
        else:
            return product['total_price']

    def get_price_product(self, product):
        """
        Функция для получения скидки на товар с учетом скидки 'Скидки на товар'
        """

        price = product['product'].discount.all().filter(
            name='DP',
        ).first().sum_discount
        if 1 <= price <= 99:
            return self.calculate_price_with_discount(product, price)

    def get_price_categories(self, product):
        """
         Функция для получения скидки на товар с учетом скидки
         'Скидки на товар', если товар относится к категории
        """

        price = (product['product'].category.discount.all()
                 .filter(name='DP')
                 .first().sum_discount)
        if 1 <= price <= 99:
            return self.calculate_price_with_discount(product, price)


class PaymentService:
    """
    Сервис оплаты
    """

    def __init__(self, order_id: int, card: str):
        self._order_id = order_id
        self._card = card

    def get_payment(self):
        """
        Меняет статус заказа
        """

        result = FakePaymentService(self._card).pay_order()

        if result == 'Оплачено':
            order = Orders.objects.get(id=self._order_id)
            if order.status_exception:
                order.status_exception = ''

            order.status = 1
            order.save()

        else:
            Orders.objects.filter(id=self._order_id).update(status=2, status_exception=result)


class FakePaymentService:
    """
    Фиктивный сервис оплаты
    """

    EXCEPTIONS = [
        _('Банк недоступен'),
        _('На счете недостаточно средств'),
        _('Введенный счет недействителен'),
        _('Оплата не выполнена')
    ]

    def __init__(self, card: str) -> str:
        self._card = card

    def pay_order(self) -> str:
        """
        Проверяет валидность номера счета или карты

        :return: статут Оплачено или имя случайной ошибки
        """

        card_cleaned = int(self._card.replace(" ", ""))

        if card_cleaned % 2 == 0 and card_cleaned % 10 != 0:
            return _('Оплачено')
        else:
            return choice(self.EXCEPTIONS)


class ProductsViewService:
    """
    Сервис просмотренных товаров
    """

    LIMIT_PRODUCTS = 20

    def __init__(self, request: HttpRequest):
        self._request = request

    def get_cached_products_id(self) -> list:
        """
        Получить список id продуктов из кэша
        """

        viewed = self._request.session.get('products_viewed')

        return viewed

    def get_viewed_product_list(self) -> list:
        """
        Получить список просмотренных продуктов
        """

        viewed_list = []
        viewed = self.get_cached_products_id()

        if viewed:
            products = Product.objects.filter(id__in=viewed)

            if products:
                products_dict = {product.id: product for product in products}
                viewed_list = [products_dict.get(product) for product in viewed]

        return viewed_list

    def add_product_to_viewed(self, product_id: int):
        """
        Добавляет id продукта в список просмотренных, который хранится в сессии.
        Если список просмотренных заполнен(равен 20) - удаляет из него самый старый просмотр.
        Если продукт уже есть в этом списке - передвигает его на место последнего просмотра.
        """

        viewed = self.get_cached_products_id()

        if viewed:
            full_list = len(viewed) == self.LIMIT_PRODUCTS
            if full_list:
                viewed.pop(0)

            if self._is_product_in_viewed_list(product_id):
                viewed = self._remove_product_from_viewed(product_id)

            viewed.append(product_id)
            self._request.session['products_viewed'] = viewed

        else:
            self._request.session['products_viewed'] = [product_id]

    def _remove_product_from_viewed(self, product_id: int) -> list:
        """
        Удалить продукт из списка просмотренных продуктов
        """

        viewed = self.get_cached_products_id()
        viewed.remove(product_id)

        return viewed

    def _is_product_in_viewed_list(self, product_id: int) -> bool:
        """
        Проверить есть ли продукт в списке просмотренных продуктов
        """

        viewed = self.get_cached_products_id()

        return product_id in viewed

    def _count_viewed_product(self) -> int:
        """
        Получить количество просмотренных продуктов
        """

        viewed = self.get_cached_products_id()
        if viewed:
            count = len(viewed)
            return count

        return 0


class ProductService:
    """
    Сервис по работе с продуктами
    """

    def __init__(self, product: Product):
        self._product = product

    def get_context(self) -> Dict:
        """
        Функция собирает контекст для рендера шаблона

        :param product: объект Product
        :return: context - контекст для рендера шаблона
        """

        context = {
            'images': self._get_images(),
            'offers': self._get_offers(),
            'feature': self._get_feature(),
        }

        return context

    def _get_images(self) -> ProductImage.objects:
        """
        Функция возвращает все изображения товара
        """

        return ProductImage.objects.filter(product=self._product)

    def _get_offers(self):
        """
        Функция возвращает всех продавцов товара
        """

        return Offer.objects.filter(product=self._product)

    def get_popular_products(self, quantity):
        popular_products = self._product.objects.filter(orders__status=True). \
                               annotate(count=Count('pk')).order_by('-count')[:quantity]
        return popular_products

    def _get_feature(self) -> dict:
        """
        Получает характеристики продукта
        """

        from compare.services import get_characteristic_from_common_info, return_model

        try:
            id_model_characteristics = self._product.feature.values()[0].get('id')
            general_characteristics = get_characteristic_from_common_info(self._product.feature.values()[0])
            try:
                model_info = return_model(self._product, id_model_characteristics)

            except ObjectDoesNotExist:
                model_info = None

            feature = {
                'characteristics': general_characteristics,
                'product_characteristic_list': model_info,
            }

            return feature

        except IndexError:
            return {}


class CategoryServices:
    """
    Сервис по работе категорий
    """

    @staticmethod
    def product_by_category(category_slug=None) -> Product.objects:
        """
        Функция отбирает продукты по категориям
        """

        products = Product.objects.filter(availability=True)
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            sub_categories = category.get_descendants(include_self=True)
            products = products.filter(category__in=sub_categories)

        return products


class CatalogService:
    """
    Сервис по работе фильтра
    """

    def catalog_processing(self, request, filterset):
        """
        Функция сортирует переданные товары и фильтрует по тегу

        :param request: объект запроса
        :param filterset: объект ProductFilter
        :return: объект ProductFilter после сортировки
        """

        if 'tag' in set(request.GET.keys()):
            filterset.queryset = self._filter_by_tags(
                filterset.queryset,
                request.GET.get('tag')
            )

        if 'sorting' in set(request.GET.keys()):
            filterset.queryset = self._sorting_products(
                request.GET.get('sorting'),
                filterset.queryset
            )

        return filterset

    @staticmethod
    def filter_products_by_name(queryset: Product.objects, name: str, value: str) -> Product.objects:
        """
        Функция фильтрует товары по имени

        :param queryset: Product objects
        :param name: имя поля фильтра
        :param value: значения поля
        """

        return queryset.filter(name__icontains=value)

    @staticmethod
    def filter_by_price(queryset: Product.objects, name: str, value: str) -> Product.objects:
        """
        Функция фильтрует товары по цене

        :param queryset: Product objects
        :param name: имя поля фильтра
        :param value: значения поля
        """

        range_list = value.split(';')
        min_price, max_price = int(range_list[0]), int(range_list[1])
        offers = Offer.objects.filter(
            unit_price__range=(min_price, max_price),
        )

        return queryset.filter(id__in=offers.values_list('product_id', flat=True))

    @staticmethod
    def filter_by_availability(queryset: Product.objects, name: str, value: str) -> Product.objects:
        """
        Функция фильтрует по доступности продукта

        :param queryset: Product objects
        :param name: имя поля фильтра
        :param value: значения поля
        """

        return queryset.filter(availability=value)

    @staticmethod
    def filter_by_delivery(queryset: Product.objects, name: str, value: str) -> Product.objects:
        """
        Функция фильтрует товары по способу доставки

        :param queryset: Product objects
        :param name: имя поля фильтра
        :param value: значения поля
        """

        delivery_type = 1

        if value == 'False':
            delivery_type = 2

        return queryset.filter(offers__seller__store_settings__delivery_type=delivery_type)

    @staticmethod
    def filter_by_stores(queryset: Product.objects, name: str, value: str) -> Product.objects:
        """
        Функция фильтрует товары по продавцу

        :param queryset: Product objects
        :param name: имя поля фильтра
        :param value: значения поля
        """

        if value:
            offers = Offer.objects.filter(seller__in=value)

            return queryset.filter(id__in=offers.values_list('product_id', flat=True))

        return queryset

    @staticmethod
    def filter_by_feature(queryset: Product.objects, name: str, value: str) -> Product.objects:
        """
        Функция фильтрует товары по характеристикам

        :param queryset: Product objects
        :param name: имя поля фильтра
        :param value: значения поля
        """

        return queryset.filter(feature__icontains=value)

    @staticmethod
    def _filter_by_tags(queryset: Product.objects, value: str) -> Product.objects:
        """
        Функция фильтрует товары по переданному тегу

        :param queryset: Product objects
        :param value: имя тега
        """

        return queryset.filter(tags__name=value)

    @staticmethod
    def get_popular_tags():
        """
        Функция отбирает популярные теги по частоте купленных товаров
        """

        tags = Tag.objects.annotate(
            count=Count(Case(
                When(products__orders__status=True, then=1),
            ))
        ).order_by('-count')

        return tags

    def _sorting_products(self, sorting: str, queryset: Product.objects) -> Product.objects:
        """
        Функция отвечает за выбор метода сортировки

        :param sorting: параметр сортировки
        """

        if 'popular' in sorting:
            queryset = self._sort_by_popularity(sorting, products=queryset)

        elif 'price' in sorting:
            queryset = self._sort_by_price(sorting, products=queryset)

        elif 'reviews' in sorting:
            queryset = self._sort_by_reviews(sorting, products=queryset)

        elif 'novelty' in sorting:
            queryset = self._sort_by_novelty(sorting, products=queryset)

        return queryset

    @staticmethod
    def _sort_by_popularity(sorting: str, products: Product.objects) -> Product.objects:
        """
        Функция сортирует продукты по популярности

        :param sorting: параметр сортировки
        """

        ordering = 'count'

        if 'down' in sorting:
            ordering = '-count'

        products = products.annotate(
            count=Count(Case(
                When(orders__status=True, then=1),
            ))
        ).order_by(ordering)

        return products

    @staticmethod
    def _sort_by_price(sorting: str, products: Product.objects) -> Product.objects:
        """
        Функция сортирует продукты по средней цене

        :param sorting: параметр сортировки
        """

        ordering = 'avg'

        if 'down' in sorting:
            ordering = '-avg'

        products = products.annotate(
            avg=Avg('offers__unit_price')
        ).order_by(ordering)

        return products

    @staticmethod
    def _sort_by_reviews(sorting: str, products: Product.objects) -> Product.objects:
        """
        Функция сортирует продукты по количеству отзывов

        :param sorting: параметр сортировки
        """

        ordering = 'count'

        if 'down' in sorting:
            ordering = '-count'

        products = products.annotate(
            count=Count('reviews')
        ).order_by(ordering)

        return products

    @staticmethod
    def _sort_by_novelty(sorting: str, products: Product.objects) -> Product.objects:
        """
        Функция сортирует продукты по дате обновления

        :param sorting: параметр сортировки
        """

        update = 'update_at'

        if 'down' in sorting:
            update = '-update_at'

        products = products.order_by(update)

        return products


class ReviewsProduct:
    """
    Сервис для добавления отзыва к товару
    """

    @staticmethod
    def add_review_to_product(request, form, slug) -> None:
        # добавить отзыв к товару

        rew = Reviews()
        rew.comment_text = form.cleaned_data['review']
        rew.product = Product.objects.get(slug=slug)
        rew.author = Profile.objects.get(user__id=request.user.id)
        rew.save()

    @staticmethod
    def get_list_of_product_reviews(product):
        # получить список отзывов к товару
        reviews = Reviews.objects.all().filter(product=product).order_by('-created_at')
        for review in reviews:
            review.created_at = review.created_at.strftime('%b %d / %Y / %H:%M')

        return reviews[0:3], reviews

    @staticmethod
    def get_number_of_reviews_for_product(product) -> int:
        # получить количество отзывов для товара
        num_reviews = len(Reviews.objects.all().filter(product=product))

        return num_reviews


class GetParamService:
    """
    Сервис, позволяющий добавлять или удалять get параметры из url
    """

    def __init__(self, url):
        self._parsed_url = urlparse(url)
        self._query = parse_qs(self._parsed_url.query, keep_blank_values=True)

    def get_url(self) -> str:
        """
        Возвращает новый url
        """

        return self._parsed_url._replace(query=urlencode(self._query, True)).geturl()

    def remove_param(self, param_name: str) -> 'GetParamService':
        """
        Удаляет get параметр из url
        """

        self._query.pop(param_name, None)
        return self

    def add_param(self, param_name: str, param_value: str) -> 'GetParamService':
        """
        Добавляет get параметр в url
        """

        self._query[param_name] = param_value
        return self


class MainService:
    """
    Класс проверки и установки продуктов в ограниченных предложениях
    """

    @staticmethod
    def get_limited_deals() -> Product:
        limited_cache = cache.get('product_limited_edition')
        if not limited_cache:

            products = Product.objects.filter(limited_edition=True).distinct('pk')
            if products:
                product_l_e = choice(products)

                product_l_e.time = datetime.now() + timedelta(days=2, hours=3)
                product_l_e.time = product_l_e.time.strftime("%d.%m.%Y %H:%M")
                cache.set('product_limited_edition', product_l_e, 86400)

                return product_l_e
        else:
            return limited_cache


class ImportProductService:
    """
    Сервис импорта продуктов из словаря.
    Продукт возможно импортировать только при существовании категории в базе данных.
    Слаг продукта считается уникальным и создается по имени продукта.
    Если такой слаг уже существует в базе данных - будет взят
    существующий продукт (без обновления полей модели Product).
    Связанные с данной моделью сущности будут обновлены, если не будет выброшено исключение.
    Данные будут сохранены или перемещены в зависимости от результата в папки import_successfully и import_failed.
    """

    file = _('Импорт файла')
    category_i = _('Категория')
    not_db = _('не найдена в базе данных')
    error = _('Ошибка')
    prod = _('Товар')
    exists_p = _('уже существует')
    no_matches = _('Нет совпадений по ключам в переданных данных')
    attention = _('Внимание')
    data = _('Данные')
    not_imported = _('не импортированы, либо импортированы не полностью')
    result_import = _('Результат импорта')
    imported_suc = _('импортирован успешно')
    failed_import = _('Не удалось переместить файл')
    directory = _('в другую директорию')
    end_imports = _('Конец импорта файла')
    error_address = _('Неправильно указан адрес для загрузки главного изображения продукта')
    error_image = _('Не удалось загрузить главное изображение для')
    failed_import_characteristics = _('Не удалось импортировать характеристики для')
    failed_import_address_images = _('Неправильно указан адрес для загрузки изображений продукта')
    failed_images = _('Не удалось загрузить изображения для')
    not_db_p = _('не найден в базе данных')
    failed_import_offer = _('Не удалось импортировать предложение от')
    fo = _('для')

    @import_logger()
    def import_product(self, file_data: list, file_name: str, file_path=None, **kwargs) -> list[str]:
        """
        Выполняет импорт продуктов.

        :param file_data: Данные файла, переданные в виде словаря.
        :param file_name: Имя файла.
        :param file_path: Путь файла, есть только, если файл передан командой и хранится в проекте,
                         поэтому по умолчанию - None.

        :return: Список, в котором содержатся сообщения о результате и/или ошибках.
        """

        initial_data = copy.deepcopy(file_data)

        log = kwargs.get('logger')
        error_message = []
        log.info(f"{self.file}: {file_name}")

        try:
            for info in file_data:
                category = None

                try:
                    category = Category.objects.get(name_ru=info['product'].get('category'))

                except Category.DoesNotExist as e:
                    error_message.append(e)
                    log.warning(f'{self.category_i} {info["product"].get("category")} {self.not_db}. {self.error}: {e}')

                if category:
                    try:
                        result = self.get_or_create_product(category, info, log)

                        if result:
                            error_message.append(result)

                    except IntegrityError as e:
                        error_message.append(e)
                        log.warning(f'{self.prod} {info.get("product").get("name")} {self.exists_p}. {self.error}: {e}')

        except KeyError as e:
            error_message.append(e)
            log.error(f'{self.no_matches}')

        if error_message:
            directory_name = 'import_failed'
            message = f'{self.attention}! {self.data} {file_name} {self.not_imported}. '
            log.info(f"{self.result_import}: {message}")

        else:
            directory_name = 'import_successfully'
            message = f'{file_name} {self.imported_suc}. '
            log.info(f"{self.result_import}: {message}")

        try:
            if file_path:
                FileMoveService(directory_name).move_file(file_path)
            else:
                FileMoveService(directory_name).save_file(initial_data, file_name)

        except Exception as e:
            log.error(f'{self.failed_import} {file_name} {self.directory}. {e}')
            error_message.append(e)

        log.info(f"{self.end_imports}: {file_name}")

        return [message, error_message]

    def get_or_create_product(self, category: Category, info: dict, log) -> Product:
        """
        Находит продукт по полю slug, либо создает новый и создает связанные сущности
        """

        error_message = []
        product_data = info.get('product')
        product_data['category'] = category
        product_data['slug'] = slugify(product_data.get('name'))

        try:
            product_data['preview'] = self.get_img_from_url(product_data['preview'])

        except ValueError as e:
            error_message.append(e)
            log.warning(f'{self.error_address} {product_data.get("name")}. {self.error}: {e}')
            product_data['preview'] = ''

        except HTTPError as e:
            error_message.append(e)
            log.warning(f'{self.error_image} {product_data.get("name")}. {self.error}: {e}')
            product_data['preview'] = ''

        product, created = Product.objects.get_or_create(slug=product_data['slug'], defaults=product_data)

        try:
            if info.get('tags'):
                tags = self.get_or_create_tags(info.get('tags'))
                product.tags.set(tags)

        except Exception as e:
            error_message.append(e)
            log.warning(f'Не удалось импортировать теги для {product.name}. Ошибка: {e}')

        try:
            self.create_feature(info.get('feature'), product, category)

        except Exception as e:
            error_message.append(e)
            log.warning(f'{self.failed_import_characteristics} {product.name}. {self.error}: {e}')

        try:
            self.create_product_images(product, info.get('images'))

        except ValueError as e:
            error_message.append(e)
            log.warning(f'{self.failed_import_address_images} {product.name}. '
                        f'{self.error}: {e}')

        except HTTPError as e:
            error_message.append(e)
            log.warning(f'{self.failed_images} {product.name}. {self.error}: {e}')

        try:
            self.create_offer(info.get('offer'), info.get('seller'), product)

        except Profile.DoesNotExist as e:
            error_message.append(e)
            log.warning(f'{info.get("seller")} {self.not_db_p}. {self.error}: {e}')

        except ValueError as e:
            error_message.append(e)
            log.warning(f'{self.failed_import_offer} {info.get("seller")} {self.fo} {product.name}. '
                        f'{self.error}: {e}')

        return error_message

    @staticmethod
    def get_or_create_tags(tags_data: list) -> list[Tag]:
        """
        Находит в базе данных теги по полю name, если совпадений нет - создает новые,
        и возвращает список Tag objects
        """

        result = [Tag.objects.get_or_create(name=tag) for tag in tags_data]
        tags = [tag[0] for tag in result]

        return tags

    @staticmethod
    def create_feature(feature_data: dict, product: Product, category: Category) -> None:
        """
        Создает характеристики продукта с учетом переданной категории
        """

        feature_data['object_id'] = product.id
        feature_data['content_type_id'] = product.feature.core_filters.get('content_type__pk')
        category_name = category.name.lower()

        if category_name == 'телевизоры':
            TVSetCharacteristic.objects.create(**feature_data)
        elif category_name == 'наушники':
            HeadphonesCharacteristic.objects.create(**feature_data)
        elif category_name == 'мобильные телефоны':
            MobileCharacteristic.objects.create(**feature_data)
        elif category_name == 'стиральные машины':
            WashMachineCharacteristic.objects.create(**feature_data)
        elif category_name == 'фотоаппараты':
            PhotoCamCharacteristic.objects.create(**feature_data)
        elif category_name == 'ноутбуки':
            NotebookCharacteristic.objects.create(**feature_data)
        elif category_name == 'электроника':
            ElectroCharacteristic.objects.create(**feature_data)
        elif category_name == 'микроволновые печи':
            MicrowaveOvenCharacteristic.objects.create(**feature_data)
        elif category_name == 'кухонная техника':
            KitchenCharacteristic.objects.create(**feature_data)
        elif category_name == 'торшеры':
            TorchereCharacteristic.objects.create(**feature_data)

    @staticmethod
    def create_offer(offer: dict, seller_name: str, product: Product) -> str:
        """
        Обновляет или создает предложение продавца на конкретный товар
        """

        seller = Profile.objects.get(name_store=seller_name)

        Offer.objects.update_or_create(
            seller=seller,
            product=product,
            defaults={
                'unit_price': offer.get('unit_price'),
                'amount': offer.get('amount'),
            },
        )

        if not product.availability:
            product.availability = True
            product.save()

    def create_product_images(self, product: Product, img_data: list) -> None:
        """
        Добавляет изображения продукта в базу данных
        """

        images = [self.get_img_from_url(img) for img in img_data]

        [
            ProductImage.objects.create(
                product=product,
                image=img,
            )
            for img in images
        ]

    @staticmethod
    def get_img_from_url(image_url: str) -> File:
        """
        Возвращает изображение из переданного url
        """

        file_name = image_url.split('/')[-1]
        img_tmp = NamedTemporaryFile(delete=True)

        with urlopen(image_url) as uo:
            assert uo.status == 200
            img_tmp.write(uo.read())
            img_tmp.flush()

        result = File(img_tmp, name=file_name)

        return result


class FileMoveService:
    """
    Сервис для сохранения и перемещения файлов внутри проекта
    """

    def __init__(self, dir_name: str):
        self.dir_name = dir_name

    def save_file(self, data: dict, file_name: str) -> None:
        """
        Сохраняет файл в соответствующую результату импорта директорию
        """

        path = 'import/' + self.dir_name + '/' + file_name

        file_path = os.path.abspath(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False)

    def move_file(self, file_path: str) -> None:
        """
        Перемещает файл в указанную директорию
        """

        dir_path = os.path.abspath('import/' + self.dir_name)

        shutil.move(file_path, dir_path)
