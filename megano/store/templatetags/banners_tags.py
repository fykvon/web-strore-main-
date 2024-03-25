from django import template
from django.http import HttpResponse
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _

from random import choices

from ..models import Banners
from ..configs import settings

register = template.Library()


@register.inclusion_tag('banner/banner_tpl_main.html')
def banner_main_page() -> dict:
    """
    Caching of random three banners is created.
    """
    try:
        banners = cache.get_or_set('banners', choices(Banners.objects.filter(is_active=True), k=3), settings.get_cache_banner())
        return {'banners': banners}
    except Exception as err:
        HttpResponse(_('Not Banners'), err)  # TODO заменить заглушку на файл с логами
