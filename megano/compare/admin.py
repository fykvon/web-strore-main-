from django.contrib.contenttypes.admin import GenericStackedInline

from .models import (
    TVSetCharacteristic,
    HeadphonesCharacteristic,
    PhotoCamCharacteristic,
    KitchenCharacteristic,
    WashMachineCharacteristic,
    NotebookCharacteristic,
    TorchereCharacteristic,
    MicrowaveOvenCharacteristic,
    MobileCharacteristic,
    ElectroCharacteristic,
    )


class AbstractCharacteristicInline(GenericStackedInline):
    model = None

    def get_extra(self, request, obj=None, **kwargs):
        if obj and obj.category:
            # Если у товара уже есть категория, то разрешаем создать только одну характеристику
            return 1
        return super().get_extra(request, obj, **kwargs)

    def get_max_num(self, request, obj=None, **kwargs):
        # Устанавливаем максимальное количество характеристик, которое можно создать
        return 1


class TVSetCharacteristicInline(AbstractCharacteristicInline):
    model = TVSetCharacteristic


class ElectroCharacteristicInline(AbstractCharacteristicInline):
    model = ElectroCharacteristic


class PhotoCamCharacteristicInline(AbstractCharacteristicInline):
    model = PhotoCamCharacteristic


class KitchenCharacteristicInline(AbstractCharacteristicInline):
    model = KitchenCharacteristic


class WashMachineCharacteristicInline(AbstractCharacteristicInline):
    model = WashMachineCharacteristic


class NotebookCharacteristicInline(AbstractCharacteristicInline):
    model = NotebookCharacteristic


class TorchereCharacteristicInline(AbstractCharacteristicInline):
    model = TorchereCharacteristic


class MicrowaveOvenCharacteristicInline(AbstractCharacteristicInline):
    model = MicrowaveOvenCharacteristic


class MobileCharacteristicInline(AbstractCharacteristicInline):
    model = MobileCharacteristic


class HeadphonesCharacteristicInline(AbstractCharacteristicInline):
    model = HeadphonesCharacteristic
