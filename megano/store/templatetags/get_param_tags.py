from django import template

from services.services import GetParamService

register = template.Library()


@register.simple_tag()
def add_get_param(url: str, param_name: str, param_value: str) -> str:
    """
    Template tag, добавляющий параметры к переданному url
    """

    return GetParamService(url).add_param(param_name, param_value).get_url()
