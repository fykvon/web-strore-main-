from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import Profile, StoreSettings

from store.models import Orders


@admin.action(description=_('Archive'))
def mark_archived(modeladmin, request, queryset):#(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet)
    queryset.update(archived=True)


@admin.action(description=_('Unarchive'))
def mark_unarchived(modeladmin, request, queryset):#(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet)
    queryset.update(archived=False)


class StoreSettingsInline(admin.TabularInline):
    model = StoreSettings
    verbose_name = _('Настройки магазина')
    verbose_name_plural = _('Настройки магазина')


@admin.register(Profile)
class AuthorAdmin(admin.ModelAdmin):
    """
      Регистрация модели профиля в админ панели.
      """
    actions = [
        mark_archived, mark_unarchived
    ]
    list_display = ['pk', 'user', 'get_html_avatar', 'role']
    list_display_links = ['pk', 'user']
    list_filter = ['archived', 'role']
    save_on_top = True
    fieldsets = [
        (None, {
            'fields': ('user', 'avatar', 'address', 'phone', 'description', 'viewed_orders', 'role', 'name_store'),
        }),
        (_('Extra options'), {
            'fields': ('archived',),
            'classes': ("collapse",)
        })]

    def get_html_avatar(self, obj):
        """
        В панели администратора,
        ссылка на изображение отображается в виде картинки размером 50х 50.
        """
        if obj.avatar:
            return mark_safe(f'<img src="{obj.avatar.url}" alt=""width="50">')

    get_html_avatar.short_description = _('Изображение')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'viewed_orders':
            if 'object_id' in request.resolver_match.captured_kwargs:
                kwargs['queryset'] = Orders.objects.filter(
                    profile_id=request.resolver_match.captured_kwargs['object_id'])
        return super(AuthorAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def get_inlines(self, request, obj):
        """
        Определяет отображение настроек магазина при выполнении условия
        """

        inlines = super().get_inlines(request, obj)

        if not obj or obj.role != 'buyer':
            inlines += (StoreSettingsInline,)

        return inlines

    def get_actions(self, request):
        """"
        Функкция удаляет 'delete_selected' из actions(действие) в панели администратора
        """
        actions = super(self.__class__, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

