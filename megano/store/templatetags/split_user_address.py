from django import template

register = template.Library()


@register.filter(name="split_string")
def split_string(value, separator) -> list:
    """
    Позволяет преобразовать строку в список по символу

    :value: string передаваемая строка.
    :separator: string символ разделитель.
    """
    data = value.split(separator)
    if len(data) > 2:
        data.append(' '.join(data[1:]))
        del data[1:3]

    return data
