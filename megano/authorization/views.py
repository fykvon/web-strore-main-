from django.contrib.auth.views import LogoutView
from django.contrib.auth import authenticate, login
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.shortcuts import reverse
from django.http import HttpResponse

from django.db import transaction
from django.db.models import Count, Case, When
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DetailView, CreateView, FormView, ListView, UpdateView

from services.check_full_name import check_name
from services.services import AuthorizationService, ProductsViewService
from .mixins import MenuMixin

from store.configs import settings
from store.models import Offer, Orders, Product

from django.core.cache import cache
from .forms import UserUpdateForm, ProfileUpdateForm, RegisterForm, LoginForm

from .models import Profile


class SellerDetail(DetailView):
    """
    Вьюшка детальной страницы продавца
    """

    model = Profile
    template_name = 'authorization/about-seller.html'
    context_object_name = 'seller'

    def get_object(self, *args, **kwargs) -> Profile.objects:
        """
        Находит профиль продавца по слагу
        """

        slug = self.kwargs.get('slug')
        instance = Profile.objects.get(slug=slug)
        profile = cache.get_or_set(f'profile-{slug}', instance, settings.get_cache_seller())

        return profile

    def get_context_data(self, **kwargs):
        """
        Передает в контекст топ товаров продавца
        """

        context = super().get_context_data(**kwargs)

        context['top_offers'] = Offer.objects.filter(
            seller=context.get('object')
        ).annotate(
            count=Count(Case(
                When(product__orders__status=True, then=1),
            ))
        ).order_by('-count')[:10]

        return context


class ProfileOrders(ListView, MenuMixin):
    """
    Представление для просмотра заказов профиля
    """
    model = Profile
    template_name = 'authorization/history_orders.html'

    def get_context_data(self, **kwargs):
        """
        Функция возвращает контекст
        """
        context = super().get_context_data(**kwargs)
        context['orders'] = Orders.objects.filter(profile=self.request.user.profile.id).order_by('-created_at')[:20]
        context.update(
            self.get_menu(id='3'),
        )
        return context


class ProfileDetailView(MenuMixin, DetailView):
    """
    Представление для просмотра профиля
    """
    profile_page = _('Страница пользователя')

    model = Profile
    template_name = 'authorization/profile_detail.html'

    def get_object(self, *args, **kwargs):
        """
        Находит профиль продавца по слагу
        """
        if self.request.user.is_authenticated:
            slug = self.kwargs.get('slug')
            instance = Profile.objects.get(slug=slug)
            profile = cache.get_or_set(f'profile-{slug}', instance, settings.get_cache_seller())
            return profile
        else:
            return redirect(reverse_lazy("profile:login"))

    def get_context_data(self, **kwargs) -> HttpResponse:
        """
        Функция возвращает контекст
        """
        if self.request.user.is_authenticated:
            context = super().get_context_data(**kwargs)
            context.update(
                self.get_menu(id='1')
            )
            context['order'] = Orders.objects.filter(profile=self.request.user.profile.id).order_by('-created_at')[:1]
            context['title'] = f'{self.profile_page}: {self.request.user.username}'
            return context


class ProfileUpdateView(MenuMixin, UpdateView):
    """
   Представление для редактирования профиля
   """
    update_profile_page = _('Редактирование страницы пользователя')

    model = Profile
    form_class = ProfileUpdateForm
    template_name = 'authorization/profile_update_form.html'

    def get_success_url(self):
        return reverse(
            'profile:profile',
            kwargs={'slug': self.request.user.profile.slug},
        )

    def form_valid(self, form):
        """"
        Функция обрабатывает валидную форму
        """
        context = self.get_context_data()
        user_form = context['user_form']
        with transaction.atomic():
            if all([form.is_valid(), user_form.is_valid()]):
                user = self.request.user
                user.first_name, user.last_name = check_name(user_form.cleaned_data['name'])
                user.email = user_form.cleaned_data['email']
                user.set_password(user_form.cleaned_data['password'])
                form.save()
                user.save()
            else:
                context.update({'user_form': user_form})
                return render(self.request, 'authorization/profile_update_form.html', context=context)
        user = authenticate(username=user.username, password=user.password)
        login(self.request, user)
        messages.success(self.request, _('Профиль успешно сохранен '))
        return super().form_valid(form)

    def form_invalid(self, form, *args, **kwargs):
        """"
        Функция обрабатывает невалидную форму
        """
        context = self.get_context_data()
        context.update(
            {'error': _("Некорректный ввод данных. Попробуйте еще раз.")}
        )

        return render(self.request, 'authorization/profile_update_form.html', context=context)

    def get_context_data(self, **kwargs):
        """
        Функция возвращает контекст
        """
        context = super(ProfileUpdateView, self).get_context_data(**kwargs)
        context.update(
            self.get_menu(id='2'),
        )
        context['title'] = f'{self.update_profile_page}: {self.request.user.username}'
        if self.request.POST:
            context['user_form'] = UserUpdateForm(self.request.POST, instance=self.request.user)
        else:
            context['user_form'] = UserUpdateForm(instance=self.request.user)

        return context


class ProfileOrderPage(DetailView):
    """
    Представление для просмотра детализации заказов профиля
    """
    model = Orders
    template_name = 'authorization/detailed_order_page.html'

    def get_context_data(self, **kwargs):
        """
        Функция возвращает контекст
        """
        context = super().get_context_data(**kwargs)
        context['order'] = Orders.objects.get(id=self.kwargs['pk'])
        return context


class ProfileHistoryView(ListView, MenuMixin):
    """
    Представление истории просмотров профиля
    """

    model = Product
    template_name = 'authorization/history_view.html'
    context_object_name = 'products'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            self.get_menu(id='4'),
        )
        context['products'] = ProductsViewService(self.request).get_viewed_product_list()

        return context


class RegisterView(CreateView):
    """
    Вьюшка страницы регистрации
    """
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('store:index')

    def form_valid(self, form: RegisterForm):
        """
        Если удалось зарегистрировать пользователя - авторизует и отправляет на главную страницу,
        иначе возвращает форму и ошибку
        """

        result = AuthorizationService().register_new_user(self.request, form)

        if result is True:
            return super().form_valid(form)

        context = {
            'error': _('Указанный email уже зарегистрирован'),
            'form': form,
        }
        return render(self.request, 'registration/register.html', context=context)


class UserLoginView(FormView):
    """
    Вьюшка страницы авторизации
    """

    form_class = LoginForm
    template_name = 'registration/login.html'
    success_url = reverse_lazy('store:index')

    def form_valid(self, form: LoginForm):
        """
        Если удалось авторизоваться - отправляет на главную страницу,
        иначе возвращает форму и ошибку
        """

        result = AuthorizationService().get_login(self.request, form)

        if result is True:
            return super().form_valid(form)

        else:
            context = {
                'form': form,
                'error': result,
            }
            return render(self.request, 'registration/login.html', context=context)


class UserLogoutView(LogoutView):
    """
    Осуществляет выход пользователя из аккаунта с редиректом на главную страницу
    """

    next_page = reverse_lazy('store:index')
