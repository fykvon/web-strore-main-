from django.core.cache import cache


class Message:
    """
    Класс всплывающего сообщения
    """

    def __init__(self):
        self.title = str()
        self.text = str()


class ToastMessage:
    """
    Класс для создания всплывающих сообщений и сохранения их в кэш
    """

    @staticmethod
    def get() -> cache:
        # Функции запроса кэша

        return cache.get('toast_message')

    @staticmethod
    def toast_message(title: str, text: str) -> None:
        # создание сообщения и отправка в кэш
        message = Message()
        message.title = title
        message.text = text

        def cache_message_set(cache_list: list, message: Message) -> None:
            # Сохранение кэша
            cache_list.append(message)
            cache.set('toast_message', cache_list, 1)

        cache_list = cache.get('toast_message')
        if cache_list:
            cache_message_set(cache_list, message)
        else:
            cache_message_set(cache_list=list(), message=message)
