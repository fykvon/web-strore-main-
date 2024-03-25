from django import template

register = template.Library()


@register.filter()
def converter_to_int(value):
    """
    Преобразователь строки в число.
    """
    return int(value)
