from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from imagekit.models import ProcessedImageField
from pilkit.processors import ResizeToFit

from services.slugify import slugify


class BaseModel(models.Model):
    """"
    Базовый класс модели
    """

    def delete(self, *arg, **kwargs):
        """"
        Функция, меняющая поведение delete на мягкое удаление
        """
        self.archived = True
        self.save()
        return self

    class Meta:
        abstract = True


def profile_images_directory_path(instance: 'Profile', filename: str) -> str:
    """
    Функция генерирует путь сохранения изображений с привязкой к id товара

    :param instance: объект ProductImage
    :param filename: имя файла
    :return: str - путь для сохранения
    """

    return f'profiles/profile_{instance.id}/{filename}'


class Profile(BaseModel):
    """
    Модель профиля всех пользователей
    """

    class Role(models.TextChoices):
        """
        Модель ролей пользователей
        """

        ADMIN = 'admin'
        STORE = 'store'
        BUYER = 'buyer'

    user = models.OneToOneField(User, verbose_name=_('Пользователь'), on_delete=models.CASCADE)
    slug = models.SlugField(_('Слаг'), max_length=150, default='', null=True, blank=True)
    phone = models.CharField(_('Teleфон'), null=True, blank=True, unique=True)
    description = models.CharField(_('Описание'), max_length=100)
    avatar = ProcessedImageField(
        blank=True,
        verbose_name=_('Фотография профиля'),
        upload_to=profile_images_directory_path,
        options={"quality": 80},
        processors=[ResizeToFit(200, 155, mat_color='white')],
        null=True
    )
    archived = models.BooleanField(default=False, verbose_name=_('Архивация'))
    name_store = models.CharField(_('Имя магазина'), max_length=50, blank=True, null=True)
    address = models.CharField(_('Адрес'), max_length=100)
    viewed_orders = models.ForeignKey(
        'store.Product',
        verbose_name=_('Связанные заказы'),
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    role = models.CharField(_('Роль'), default=Role.BUYER, choices=Role.choices)

    def __str__(self) -> str:
        return f'{self.user}'

    def save(self, *args, **kwargs):
        if self.role == 'store' and self.name_store:
            self.slug = slugify(self.name_store)
        else:
            self.slug = slugify(self.user.username)

        super(Profile, self).save(*args, **kwargs)

    class Meta:
        db_table = 'Profiles'
        ordering = ['id', 'user']
        verbose_name = _('Профиль')
        verbose_name_plural = _('Профили')
        permissions = (
            ('store', 'has offers for sale'),
            ('user', 'all site users'),
            ('buyer', 'only buys goods'),
            ('admin', 'manages the site'),
        )


class StoreSettings(models.Model):
    """
    Модель настроек магазина
    """

    class Delivery(models.IntegerChoices):
        """
        Модель вариантов доставки
        """

        FREE = 1, _('Обычная доставка')
        EXPRESS = 2, _('Экспресс-доставка')

        __empty__ = _('Выберите доставку')

    class Payment(models.IntegerChoices):
        """
        Модель вариантов оплаты
        """

        OWN_CARD = 1, _('Онлайн картой')
        ANOTHER_CARD = 2, _('Онлайн со случайного счета')

        __empty__ = _('Выберите оплату')

    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='store_settings')
    delivery_type = models.IntegerField(_('Способ доставки'), choices=Delivery.choices)
    payment = models.IntegerField(_('Способ оплаты'), choices=Payment.choices)

    def __str__(self) -> str:
        return f"{self.profile.name_store}"

    class Meta:
        db_table = 'StoreSettings'
        ordering = ['id', 'profile']
        verbose_name = _('Настройки магазина')
        verbose_name_plural = _('Настройки магазина')
