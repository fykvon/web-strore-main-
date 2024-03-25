import json

from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.core.management.base import BaseCommand
from store.tasks import import_product_from_command

import os
import re

from store.utils import busy_queues


class Command(BaseCommand):
    """
    Класс позволяет запустить команду для загрузки файла из консоли.
    Пример: python manage.py upload_file <file_name>
    """
    help = "Позволяет загрузить файл в бд"

    def add_arguments(self, parser):
        parser.add_argument(
            'file',
            type=str,
            help=_("Указывает имя файла")
        )
        parser.add_argument(
            'email',
            type=str,
            help=_("Указывает адресата для отправки сообщений на почту")
        )

    def handle(self, *args, **options):
        path_work_dir = os.path.abspath(os.path.join('import'))
        file_name = options.get('file')
        address = options.get('email')
        file = self.search_file(path_work_dir, file_name)

        if busy_queues('json_import'):
            self.stdout.write(f'Ошибка: предыдущий импорт ещё не выполнен. Пожалуйста, дождитесь его окончания.')
        else:
            for _file in file:
                name_file = self.cleaned_name(_file)
                with open(_file, 'r', encoding='utf-8') as file_json:
                    try:
                        file_content = file_json.read()
                        data_list = json.loads(file_content)

                        task_result = import_product_from_command.apply_async(
                            kwargs={
                                'file_data': data_list,
                                'name': name_file,
                                'email': address,
                                'file_path': _file,
                            },
                            queue='json_import',
                        )

                        cache.set('task_id', task_result.id)
                        self.stdout.write(f'{name_file} добавлен в загрузку.')

                    except Exception as err:
                        self.stdout.write(f'Команда "upload_file" для файла {name_file} завершилась с ошибкой.\n'
                                          f'ОШИБКА: {err}')

    @staticmethod
    def search_file(path_work_dir, file_name):
        """
        Поиск файла по названию или в переданной директории
        """
        file_list = []
        dir_name = os.path.isdir(os.path.join(path_work_dir, file_name))
        if dir_name:
            path_work_dir = os.path.abspath(os.path.join(path_work_dir, file_name))

        for root, dirs, files in os.walk(path_work_dir):
            for file in files:
                if dir_name:
                    if re.findall(r'.json', file):
                        file_list.append(os.path.join(root, file))
                if file_name in files:
                    file_list.append(os.path.join(root, file_name))
                    break
        return file_list

    @staticmethod
    def cleaned_name(file):
        """
        Очистка файля от расширения
        """
        name = re.findall(r'[^\\/]+', file)[-1].split('.')[0]
        return name
