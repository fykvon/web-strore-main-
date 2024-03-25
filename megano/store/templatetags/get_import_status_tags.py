from celery.result import AsyncResult
from django import template
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.simple_tag()
def get_import_status() -> str:
    """
    Получает статус выполнения импорта, если он есть
    """

    task_id = cache.get('task_id')

    if task_id:
        result = AsyncResult(task_id)
        if result.ready():
            if result.successful():
                return _('Выполнен успешно')

            return _('Завершен с ошибкой')

        return _('В процессе выполнения')

    return _('Не было ни одного импорта')
