from modeltranslation.translator import register, TranslationOptions
from compare.models import (AbstractCharacteristicModel,
                            TVSetCharacteristic,
                            HeadphonesCharacteristic,
                            WashMachineCharacteristic,
                            MobileCharacteristic,
                            PhotoCamCharacteristic,
                            MicrowaveOvenCharacteristic,
                            KitchenCharacteristic,
                            TorchereCharacteristic,
                            NotebookCharacteristic,
                            ElectroCharacteristic,
                            )


@register(AbstractCharacteristicModel)
class AbstractCharacteristicModelTranslationOptions(TranslationOptions):
    fields = ('made_in', 'color',)


@register(TVSetCharacteristic)
class TVSetCharacteristicTranslationOptions(TranslationOptions):
    fields = ('name', 'country', 'wi_fi', 'hdmi', 'description',)


@register(HeadphonesCharacteristic)
class HeadphonesCharacteristicTranslationOptions(TranslationOptions):
    fields = ('wireless', 'mic', 'fit', 'bluetooth', 'hdmi', 'description',)


@register(WashMachineCharacteristic)
class WashMachineCharacteristicTranslationOptions(TranslationOptions):
    fields = ('type_loading', 'description',)


@register(MobileCharacteristic)
class MobileCharacteristicTranslationOptions(TranslationOptions):
    fields = ('phone_type',)


@register(PhotoCamCharacteristic)
class PhotoCamCharacteristicTranslationOptions(TranslationOptions):
    fields = ('type',)


@register(MicrowaveOvenCharacteristic)
class MicrowaveOvenCharacteristicTranslationOptions(TranslationOptions):
    fields = ('grill',)


@register(KitchenCharacteristic)
class KitchenCharacteristicTranslationOptions(TranslationOptions):
    fields = ('type', 'description',)


@register(TorchereCharacteristic)
class TorchereCharacteristicTranslationOptions(TranslationOptions):
    fields = ('led_type', 'place_type',)


@register(NotebookCharacteristic)
class NotebookCharacteristicTranslationOptions(TranslationOptions):
    fields = ('laptop_type',)


@register(ElectroCharacteristic)
class ElectroCharacteristicTranslationOptions(TranslationOptions):
    fields = ('type_product', 'description',)
