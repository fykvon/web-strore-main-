from django import template

register = template.Library()


@register.simple_tag()
def change_phone_format(phone: str) -> str:
    """
    Template tag, изменяющий формат вывода телефона на '(___)______'
    """

    new_format = f'({phone[:3]}) {phone[3:]}'

    return new_format
