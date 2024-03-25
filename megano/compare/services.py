from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from compare.models import (HeadphonesCharacteristic,
                            TVSetCharacteristic,
                            WashMachineCharacteristic,
                            MobileCharacteristic,
                            PhotoCamCharacteristic,
                            NotebookCharacteristic,
                            KitchenCharacteristic,
                            TorchereCharacteristic,
                            ElectroCharacteristic,
                            MicrowaveOvenCharacteristic,
                            )

from store.models import Product

"""
Сервис по работе списка сравнений
"""


def _add_product_to_comparison(request: WSGIRequest, comparison_id) -> HttpResponseRedirect:
    """
    Добавить одну единицу товара в корзине

    :param request: запрос
    :param slug: slug товара
    :return: HttpResponse - текущая страница
    """

    if request.user.is_authenticated:
        # Если пользователь авторизован, используем сессии
        comparison_list = request.session.get('comparison_list', [])
    else:
        # Если пользователь не авторизован, используем куки
        comparison_list = request.COOKIES.get('comparison_list', '').split(',')
    # Проверка, чтобы не было больше 4 продуктов для сравнения и не добавлять 1 товар несколько раз
    if len(set(comparison_list)) >= 4:
        comparison_list.pop(0)
    # Проверка, чтобы избежать добавления одного товара несколько раз
    if comparison_id not in comparison_list:
        comparison_list.append(comparison_id)

        if request.user.is_authenticated:
            # Если пользователь авторизован, сохраняем в сессию
            request.session['comparison_list'] = comparison_list
        else:
            # Если пользователь не авторизован, сохраняем в куки
            response = redirect(request.META.get('HTTP_REFERER'))
            response.set_cookie('comparison_list', ','.join(comparison_list))
            return response
    return redirect(request.META.get('HTTP_REFERER'))

def _remove_product_from_comparison(request):
    """
    Добавить одну единицу товара в корзине

    :param request: запрос
    :return: HttpResponse - текущая страница
    """

    if request.user.is_authenticated:
        # Если пользователь авторизован, очищаем сессию
        request.session['comparison_list'] = []
    else:
        # Если пользователь не авторизован, очищаем куки
        response = redirect(request.META.get('HTTP_REFERER'))
        response.delete_cookie('comparison_list')
        return response

    return redirect('store:comparison')


def get_comparison_list(comparison_list):
    products = Product.objects.filter(id__in=comparison_list)
    return products


def get_compare_info(products, prev_prod_category=None) -> dict:
    result = dict()

    for product in products:
        if prev_prod_category == product.category.name or prev_prod_category == None:
            # Получение характеристик из модели в зависимости от категории по id
            id_model_characterisrics = product.feature.values()[0].get('id')
            # Получение общих характеристик в список характеристик
            general_characteristics = get_characteristic_from_common_info(product.feature.values()[0])

            # Добавление характеристик в список характеристик в зависимости от характеристик
            model_info = return_model(product, id_model_characterisrics)
            prev_prod_category = product.category.name
            product_price = product.get_average_price()
            result[product.name] = {
                'product_preview_url': product.preview.url,
                'product_slug': product.slug,
                'product_name': product.name,
                'product_category': product.category.name,
                'characterisctics': general_characteristics,
                'product_characteristic_list': model_info,
                'product_price': product_price,
                'product_offer_id': product.offers.first().id,
            }
        else:
            return redirect(reverse_lazy("compare:comparison_error"))

    return result


def return_model(product, id_model_characteristics) -> dict:
    """
    Проверка наименования категории и выбор модели
    """

    category_name = str.lower(product.category.name)
    category_list = {'наушники': 'characteristic_headset(id_model_characteristics)',
                     'телевизоры': 'characteristic_tv(id_model_characteristics)',
                     'мобильные телефоны': 'characteristic_mobile(id_model_characteristics)',
                     'стиральные машины': 'characteristic_wm(id_model_characteristics)',
                     'фотоаппараты': 'characteristic_photo(id_model_characteristics)',
                     'ноутбуки': 'characteristic_nb(id_model_characteristics)',
                     'электроника': 'characteristic_electro(id_model_characteristics)',
                     'микроволновые печи': 'characteristic_mw(id_model_characteristics)',
                     'кухонная техника': 'characteristic_kitchen_technik(id_model_characteristics)',
                     'торшеры': 'characteristic_torchere(id_model_characteristics)',
                     }

    for key, characteristic_func in category_list.items():

        if key == category_name:
            return characteristic_func


def characteristic_headset(id_model_characteristics) -> dict:
    """
    Подготовка данных для возврата на фронт
    """

    model_info = HeadphonesCharacteristic.objects.get(id=id_model_characteristics)
    characteristic = {_('Беспроводные'): model_info.wireless,
                      _('Наличие микрофона'): model_info.mic,
                      _('Ношение'): model_info.fit,
                      _('Наличие bluetooth'): model_info.bluetooth,
                      _('Сомпротивление, Ом'): model_info.resistance,
                      _('Наличие HDMI'): model_info.hdmi,
                      }
    return characteristic


def characteristic_wm(id_model_characteristics) -> dict:
    """
    Подготовка данных для возврата на фронт
    """

    model_info = WashMachineCharacteristic.objects.get(id=id_model_characteristics)
    characteristic = {_('Высота'): model_info.height,
                      -('Ширина'): model_info.width,
                      _('Глубина'): model_info.depth,
                      _('Тип загрузки'): model_info.type_loading,
                      _('Объём загрузки'): model_info.capacity,
                      _('Дополнительное описание'): model_info.description,
                      }
    return characteristic


def characteristic_mobile(id_model_characteristics) -> dict:
    """
    Подготовка данных для возврата на фронт
    """

    model_info = MobileCharacteristic.objects.get(id=id_model_characteristics)
    characteristic = {_('Тип мобильного телефона'): model_info.phone_type,
                      _('Размер экрана в дюймах'): model_info.screen_size,
                      _('Разрешение экрана'): model_info.screen_resolution,
                      _('Технология экрана'): model_info.screen_technology,
                      _('Операционная система'): model_info.op_system,
                      }
    return characteristic


def characteristic_tv(id_model_characteristics) -> dict:
    """
    Подготовка данных для возврата на фронт
    """

    model_info = TVSetCharacteristic.objects.get(id=id_model_characteristics)
    characteristic = {_('Название'): model_info.name,
                      _('Размер экрана'): model_info.screen,
                      _('Разрешение экрана'): model_info.resolution,
                      _('Страна производитель'): model_info.country,
                      _('Частота обновления'): model_info.freq,
                      _('Наличие Wi - Fi'): model_info.wi_fi,
                      _('HDMI'): model_info.hdmi,
                      _('Дополнительное описание'): model_info.description,
                      }
    return characteristic


def characteristic_photo(id_model_characteristics) -> dict:
    """
    Подготовка данных для возврата на фронт
    """

    model_info = PhotoCamCharacteristic.objects.get(id=id_model_characteristics)
    characteristic = {_('Тип фотоаппарата'): model_info.type,
                      _('Количество мегапикселей'): model_info.mp,
                      _('ISO максимальная'): model_info.max_iso,
                      _('ISO минимальная'): model_info.min_iso,
                      _('Видео разрешение'): model_info.video_resolution,
                      }
    return characteristic


def characteristic_nb(id_model_characteristics) -> dict:
    """
    Подготовка данных для возврата на фронт
    """

    model_info = NotebookCharacteristic.objects.get(id=id_model_characteristics)
    characteristic = {_('Тип ноутбука'): model_info.laptop_type,
                      _('Размер экрана в дюймах'): model_info.screen_size,
                      _('Разрешение экрана'): model_info.screen_resolution,
                      _('Плотность пикселей'): model_info.ppi,
                      _('Операционная система'): model_info.op_system,
                      _('Версия операционной системы'): model_info.op_version,
                      }
    return characteristic


def characteristic_mw(id_model_characteristics) -> dict:
    model_info = MicrowaveOvenCharacteristic.objects.get(id=id_model_characteristics)
    characteristic = {_('Объём загрузки'): model_info.capacity,
                      _('Мощность Вт'): model_info.power,
                      _('Гриль'): model_info.grill,
                      _('Высота, мм'): model_info.height,
                      _('Ширина, мм'): model_info.width,
                      _('Глубина, мм'): model_info.depth,
                      }
    return characteristic


def characteristic_kitchen_technik(id_model_characteristics) -> dict:
    """
    Подготовка данных для возврата на фронт
    """

    model_info = KitchenCharacteristic.objects.get(id=id_model_characteristics)
    characteristic = {_('Тип техники'): model_info.type,
                      _('Дополнительное описание'): model_info.description,
                      }
    return characteristic


def characteristic_electro(id_model_characteristics) -> dict:
    model_info = ElectroCharacteristic.objects.get(id=id_model_characteristics)
    characteristic = {_('Тип электроники'): model_info.type_product,
                      _('Тип питания'): model_info.power,
                      _('Дополнительное описание'): model_info.description,
                      }
    return characteristic


def characteristic_torchere(id_model_characteristics) -> dict:
    """
    Подготовка данных для возврата на фронт
    """

    model_info = TorchereCharacteristic.objects.get(id=id_model_characteristics)
    characteristic = {_('Тип лампочки'): model_info.led_type,
                      _('Высота'): model_info.height,
                      _('Место расположения'): model_info.place_type,
                      }
    return characteristic


def get_characteristic_from_common_info(data) -> dict:
    """
    Подготовка данных для возврата на фронт
    """

    characteristic_info = {_('Страна производства'): data.get('made_in'),
                           _('Год производства'): data.get('production_year'),
                           _('Цвет'): data.get('color'),
                           _('Вес'): data.get('weight'),
                           }
    return characteristic_info
