import logging
import os
from datetime import datetime
from typing import Dict, Callable
from megano.celery import app


def category_image_directory_path(instance) -> str:
    """
    Функция coздания пути к картинке категории
    """

    return f'assets/img/icons/departments/{instance.pk}.svg'


def product_images_directory_path(instance: 'ProductImage', filename: str) -> str:
    """
    Функция генерирует путь сохранения изображений с привязкой к id товара

    :param instance: объект ProductImage
    :param filename: имя файла
    :return: str - путь для сохранения
    """

    return f'products/product_{instance.product_id}/{filename}'


def jsonfield_default_description() -> Dict:
    """
    Определяет дефолтное значение поля description,
    где ожидаются данные в виде словаря, в котором:
        'card_text': [] - список строк
        'title': '' - строка
        'text_bottom': '', - строка
        'text_bottom_ul': [] - список строк
    """

    return {
        'card_text': [],
        'title': '',
        'text_bottom': '',
        'text_bottom_ul': [],
    }


def jsonfield_default_feature() -> Dict:
    """
    Определяет дефолтное значение поля feature,
    где ожидаются данные в виде - {key: value}
    """

    return {'': ''}


def discount_images_directory_path(instance: 'Discount', filename: str) -> str:
    """
    Функция генерирует путь сохранения изображений с привязкой к id скидки
    """

    return f'discount/discount{instance.id}/{filename}'


def import_logger(dir_name='logs/import_logs') -> Callable:
    """
    Декоратор, который создает логгер для переданной функции.
    Директория логов по умолчанию - logs/import_logs.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            log_dir = os.path.abspath(dir_name)

            logger = logging.getLogger('import_logger')
            logger.setLevel(logging.INFO)

            log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

            log_filename = f'import_log_{current_datetime}.log'
            file_handler = logging.FileHandler(os.path.join(log_dir, log_filename), mode='a')

            file_handler.setFormatter(log_format)
            logger.addHandler(file_handler)

            kwargs['logger'] = logger
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                result = ['Неожиданная ошибка, импорт не удался', e]
                logger.error(result)

            logger.removeHandler(file_handler)
            file_handler.close()

            return result

        return wrapper

    return decorator


def busy_queues(queue_name: str) -> bool:
    """
    Определеяет занятость, переданной очереди задач
    """

    result = app.control.inspect().active()

    if result is not None and queue_name in result:
        return True
    else:
        return False
