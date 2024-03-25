from django.utils.translation import gettext_lazy as _


class MenuMixin:

    @staticmethod
    def __menu__() -> list:
        """
        magic method with a menu list.
        :return: list of dictionaries with an available menu.
        :rtype: list
        """

        menu = [
            {'name': _('Личный кабинет'), 'url': 'profile:profile_details', 'id': '1', },
            {'name': _('Профиль'), 'url': 'profile:profile', 'id': '2', },
            {'name': _('История заказов'), 'url': 'profile:history_orders', 'id': '3', },
            {'name': _('История просмотров'), 'url': 'profile:history_view', 'id': '4', },
        ]

        return menu

    def get_menu(self, **kwargs) -> dict:
        """
        The method returns the main menu and today's date.
        :param kwargs: accepts the received dictionary.
        :rtype: dict.
        :return: returns the updated dictionary.
        :rtype: dict.
        """

        context = kwargs
        context.update(
            menu=self.__menu__(),
        )

        return context
