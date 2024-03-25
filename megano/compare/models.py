from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.db import models


class AbstractCharacteristicModel(models.Model):
    """
    Общая модель характеристик
    """

    made_in = models.CharField(max_length=30, verbose_name=_('Сделан в '), null=True, blank=True)
    production_year = models.IntegerField(verbose_name=_('В каком году произведен'), null=True, blank=True)
    color = models.CharField(max_length=15, verbose_name=_('Цвет'), null=True, blank=True)
    weight = models.CharField(verbose_name=_('Вес'), null=True, blank=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['id', ]
        verbose_name = _('Абстрактные характеристики')
        verbose_name_plural = _('Абстрактные характеристики')


class TVSetCharacteristic(AbstractCharacteristicModel):
    """
    Характеристики Телевизора
    """

    name = models.TextField(default=_('TVSet'), null=True, blank=True)
    screen = models.CharField(null=True, blank=True, max_length=10, verbose_name=_('Размер экрана'))
    resolution = models.CharField(null=True, blank=True, max_length=10, verbose_name=_('Разрешение экрана'))
    country = models.CharField(null=True, blank=True, max_length=25, verbose_name=_('Страна производитель'))
    freq = models.IntegerField(null=True, blank=True, verbose_name=_('Частота обновления'))
    wi_fi = models.CharField(max_length=20, verbose_name=_('Наличие Wi-Fi'), default=_('Нет'))
    hdmi = models.CharField(max_length=20, verbose_name='HDMI', default=_('Нет'))
    description = models.TextField(verbose_name=_('Дополнительное описание'))

    class Meta:
        ordering = ['id', ]
        verbose_name = _('Характеристики телевизора')
        verbose_name_plural = _('Характеристики телевизоров')


class HeadphonesCharacteristic(AbstractCharacteristicModel):
    """
    Характеристики Наушников
    """

    wireless = models.CharField(max_length=20, verbose_name=_('Беспроводные'), default=_('Нет'))
    mic = models.CharField(max_length=20, verbose_name=_('Микрофон'), default=_('Нет'))
    fit = models.CharField(max_length=20, verbose_name=_('Как носить'))
    bluetooth = models.CharField(max_length=20, verbose_name=_('Наличие Bluetooth'), default=_('Нет'))
    resistance = models.IntegerField(verbose_name=_('Сопротивление (Ом)'), null=True, blank=True)
    hdmi = models.CharField(max_length=20, verbose_name='HDMI', default=_('Нет'))
    description = models.TextField(null=True, blank=True, verbose_name=_('Дополнительное описание'))

    class Meta:
        ordering = ['id', ]
        verbose_name = _('Характеристики наушников')
        verbose_name_plural = _('Характеристики наушников')


class WashMachineCharacteristic(AbstractCharacteristicModel):
    """
    Характеристики Стиральной машины
    """

    height = models.IntegerField(null=True, blank=True, verbose_name=_('Высота'))
    width = models.IntegerField(null=True, blank=True, verbose_name=_('Ширина'))
    depth = models.IntegerField(null=True, blank=True, verbose_name=_('Глубина'))
    type_loading = models.CharField(max_length=20, verbose_name=_('Тип загрузки'), default=_('Информации нет'))
    capacity = models.IntegerField(null=True, blank=True, verbose_name=_('Объём загрузки'))
    description = models.TextField(null=True, blank=True, verbose_name=_('Дополнительное описание'))

    class Meta:
        ordering = ['id', ]
        verbose_name = _('Характеристики стиральной машины')
        verbose_name_plural = _('Характеристики стиральных машин')


class MobileCharacteristic(AbstractCharacteristicModel):
    """
    Модель характеристик мобильного телефона
    """

    phone_type = models.CharField(max_length=20, verbose_name=_('Тип мобильного телефона'))
    screen_size = models.IntegerField(null=True, blank=True, verbose_name=_('Размер экрана в дюймах'))
    screen_resolution = models.CharField(null=True, blank=True, verbose_name=_('Разрешение экрана'))
    screen_technology = models.CharField(max_length=10, verbose_name=_('Технология экрана'), null=True, blank=True)
    op_system = models.CharField(max_length=20, verbose_name=_('Операционная система'), default=_('Информации нет'))

    class Meta:
        ordering = ['id', ]
        verbose_name = _('Характеристики телефона')
        verbose_name_plural = _('Характеристики телефонов')


class PhotoCamCharacteristic(AbstractCharacteristicModel):
    """
    Модель характеристик фотоаппарата
    """

    type = models.CharField(max_length=30, verbose_name=_('Тип фотоаппарата'), default=_('Информации нет'))
    mp = models.IntegerField(verbose_name=_('Количество мегапикселей'), null=True, blank=True)
    max_iso = models.IntegerField(verbose_name=_('ISO максимальная'), null=True, blank=True)
    min_iso = models.IntegerField(verbose_name=_('ISO минимальная'), null=True, blank=True)
    video_resolution = models.IntegerField(verbose_name=_('Видео разрешение'), null=True, blank=True)

    class Meta:
        ordering = ['id', ]
        verbose_name = _('Характеристики фотоаппарата')
        verbose_name_plural = _('Характеристики фотоаппаратов')


class MicrowaveOvenCharacteristic(AbstractCharacteristicModel):
    """
    Модель характеристик микроволновки
    """

    capacity = models.IntegerField(null=True, blank=True, verbose_name=_('Объём загрузки'))
    power = models.IntegerField(null=True, blank=True, verbose_name=_('Мощность Вт'))
    grill = models.CharField(max_length=30, default=_('Информации нет'))
    height = models.IntegerField(null=True, blank=True, verbose_name=_('Высота'))
    width = models.IntegerField(null=True, blank=True, verbose_name=_('Ширина'))
    depth = models.IntegerField(null=True, blank=True, verbose_name=_('Глубина'))

    class Meta:
        ordering = ['id', ]
        verbose_name = _('Характеристики микроволновой печи')
        verbose_name_plural = _('Характеристики микроволновых печей')


class KitchenCharacteristic(AbstractCharacteristicModel):
    """
    Модель характеристик кухонного электронного прибора
    """

    type = models.CharField(max_length=20, blank=True, verbose_name=_('Тип техники'))
    description = models.TextField(null=True, blank=True, verbose_name=_('Дополнительное описание'))

    class Meta:
        ordering = ['id', ]
        verbose_name = _('Характеристики кухонной техники')
        verbose_name_plural = _('Характеристики кухонной техники')


class TorchereCharacteristic(AbstractCharacteristicModel):
    """
    Модель характеристик торшера
    """

    led_type = models.CharField(max_length=20, null=True, blank=True, verbose_name=_('Тип лампочки'))
    place_type = models.CharField(max_length=30, null=True, blank=True, verbose_name=_('Место расположения'))
    height = models.IntegerField(null=True, blank=True, verbose_name=_('Высота'))

    class Meta:
        ordering = ['id', ]
        verbose_name = _('Характеристики торшера')
        verbose_name_plural = _('Характеристики торшеров')


class NotebookCharacteristic(AbstractCharacteristicModel):
    """
    Модель характеристик ноутбука
    """

    laptop_type = models.CharField(max_length=20, default=_('Информации нет'), verbose_name=_('Тип ноутбука'))
    screen_size = models.IntegerField(null=True, blank=True, verbose_name=_('Размер экрана в дюймах'))
    screen_resolution = models.CharField(null=True, blank=True, verbose_name=_('Разрешение экрана'))
    ppi = models.IntegerField(null=True, blank=True, verbose_name=_('Плотность пикселей'))
    op_system = models.CharField(max_length=20, verbose_name=_('Операционная система'), default=_('Информации нет'))
    op_version = models.CharField(null=True, blank=True, max_length=15, verbose_name=_('Версия операционной системы'))

    class Meta:
        ordering = ['id', ]
        verbose_name = _('Характеристики ноутбука')
        verbose_name_plural = _('Характеристики ноутбуков')


class ElectroCharacteristic(AbstractCharacteristicModel):
    """
    Модель характеристик электирческого прибора
    """

    type_product = models.CharField(max_length=20, default=_('Информации нет'), verbose_name=_('Тип электроники'))
    power = models.CharField(max_length=30, null=True, blank=True, verbose_name=_('Тип питания'))
    description = models.TextField(null=True, blank=True, verbose_name=_('Дополнительное описание'))

    class Meta:
        ordering = ['id', ]
        verbose_name = _('Характеристики электроники')
        verbose_name_plural = _('Характеристики электроники')
