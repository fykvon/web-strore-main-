"""
Модуль с настройками сайта
"""
from __future__ import annotations
from django.utils.translation import gettext_lazy as _

SECOND = 60
HOURS = 60 * 60
DAYS = 60 * 60 * 24


class Settings:
    """
    Класс с настройками сайта.
    Обновление названия магазина.
    Обновление время кэширования для Баннера, корзины, детализации продуктов, каталога
    """

    def __init__(self):
        """ Значения по умолчанию """
        self.__site_name = 'Megano'
        self.__cache_banner = SECOND * 10  # 10 min
        self.__cache_cart = SECOND * 10  # 10 min
        self.__cache_product = DAYS  # 1 day
        self.__cache_seller = DAYS  # 1 day
        self.__cache_catalog = DAYS  # 1 day
        self.__get_filter_params = DAYS  # 1 day

    @staticmethod
    def time_calculate(cache_time) -> str:
        """
        Расчет времени и вывод значений по минутам, часам и дням
        """

        minute = _(' мин.')
        hour = _('ч.')
        day = _('д.')

        days = cache_time // DAYS
        hours = (cache_time // SECOND) // SECOND  # hours
        minutes = (cache_time // SECOND) % SECOND  # minutes
        if cache_time // SECOND < SECOND:
            return f"{cache_time // SECOND} {minute}"
        elif 60 <= cache_time // SECOND < 1440:
            return (f"{hours}{hour}. "
                    f"{str(minutes) + {minute} if minutes != 0 else ''}"
                    )
        elif 1440 <= cache_time // SECOND:
            _hours = (cache_time % DAYS) // HOURS
            _minutes = ((cache_time % DAYS) % HOURS) // SECOND
            return (f"{days}{day} "
                    f"{str(_hours) + {hour} if _hours != 0 else ''} "
                    f"{str(_minutes) + {minute} if _minutes != 0 else ''}"
                    )

    def set_site_name(self, name: str) -> None:
        """
        Устанавливает название магазина

        :param name: str: вывеска магазина.
        """

        self.__site_name = name

    def set_cache_banner(self, time_cache: int) -> None:
        """
        Устанавливает время кэширование Баннера.

        :param time_cache: int время в минутах
        """

        self.__cache_banner = int(time_cache) * SECOND

    def set_cache_cart(self, time_cache: int) -> None:
        """
        Устанавливает время кэширование Корзины.

        :param time_cache: int время в минутах
        """

        self.__cache_cart = int(time_cache) * SECOND

    def set_cache_product_detail(self, time_cache: int) -> None:
        """
        Устанавливает время кэширования детальной информации продукта.

        :param time_cache:  int время в минутах
        """

        self.__cache_product = int(time_cache) * SECOND

    def set_cache_seller(self, time_cache: int) -> None:
        """
        Устанавливает время кэширования детальной информации продавца

        :param time_cache:  int время в минутах
        """

        self.__cache_seller = int(time_cache) * SECOND

    def set_cache_catalog(self, time_cache: int) -> None:
        """
        Устанавливает время кэширования каталога.

        :param time_cache:  int время в минутах
        """

        self.__cache_catalog = int(time_cache) * SECOND

    def set_cache_filter_params(self, time_cache: int) -> None:
        """
        Устанавливает время кэширования параметров фильтра.

        :param time_cache:  int время в минутах
        """

        self.__get_filter_params = int(time_cache) * SECOND

    def get_site_name(self) -> str:
        """
        Возвращает название магазина

        :return: str
        """

        return self.__site_name

    def get_cache_banner(self, time: bool = True) -> int | str:
        """
        Возвращает время хранения кэша Баннера.

        :time: bool, если time == True, то время возвращается как число, иначе как форматированный вывод.
        :return: int или str время в минутах.
        """

        if time:
            return self.__cache_banner

        return self.time_calculate(self.__cache_banner)

    def get_cache_cart(self, time: bool = True) -> int | str:
        """
        Возвращает время хранения кэша Корзины.

        :time: bool Если time == True, то время возвращается как число, иначе как форматированный вывод.
        :return: int или str время в минутах.
        """

        if time:
            return self.__cache_cart

        return self.time_calculate(self.__cache_cart)

    def get_cache_product_detail(self, time: bool = True) -> int | str:
        """
        Возвращает время хранения кэша детальной информации Продукта.

        :time: bool Если time == True, то время возвращается как число, иначе как форматированный вывод.
        :return: int или str время в минутах.
        """

        if time:
            return self.__cache_product

        return self.time_calculate(self.__cache_product)

    def get_cache_seller(self, time: bool = True) -> int | str:
        """
        Возвращает время хранения кэша данных о продавце.

        :time: bool Если time == True, то время возвращается как число, иначе как форматированный вывод.
        :return: int или str время в минутах.
        """

        if time:
            return self.__cache_seller

        return self.time_calculate(self.__cache_seller)

    def get_cache_catalog(self, time: bool = True) -> int | str:
        """
        Возвращает время хранения кэша данных каталога

        :time: bool Если time == True, то время возвращается как число, иначе как форматированный вывод.
        :return: int или str время в минутах.
        """

        if time:
            return self.__cache_catalog

        return self.time_calculate(self.__cache_catalog)

    def get_cache_filter_params(self, time: bool = True) -> int | str:
        """
        Возвращает время хранения кэша параметров фильтра

        :time: bool Если time == True, то время возвращается как число, иначе как форматированный вывод.
        :return: int или str время в минутах.
        """

        if time:
            return self.__get_filter_params

        return self.time_calculate(self.__get_filter_params)

    def set_popular_products_cache(self, time_cache):
        self.__cache_product = int(time_cache) * DAYS

    def get_popular_products_cache(self, time: bool = True):
        """
        Возвращает время хранения кэша данных популярных продуктов.

        :time: bool Если time == True, то время возвращается как число, иначе как форматированный вывод.
        :return: int или str время в минутах.
        """

        if time:
            return self.__cache_product

        return self.time_calculate(self.__cache_product)


settings = Settings()
