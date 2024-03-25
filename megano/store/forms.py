from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from multiupload.fields import MultiFileField

from authorization.models import Profile
from .models import Orders, Product


class ReviewsForm(forms.Form):
    review = forms.CharField(widget=forms.Textarea, max_length=100)


class OrderCreateForm(forms.ModelForm):
    """
    Класс формы для оформления Заказа.
    """

    name_placeholder = _("Иванов Иван Иванович")

    name = forms.CharField(
        max_length=100,
        label='ФИО',
        widget=forms.TextInput(attrs={
            'class': "form-input",
            'id': "name",
            'name': "name",
            'type': "text",
            'placeholder': name_placeholder,
        }),
    )
    phone = forms.CharField(
        max_length=20,
        label='Телефон',
        widget=forms.TextInput(attrs={
            'class': "form-input",
            'id': "phone",
            'name': "phone",
            'type': "text",
            'placeholder': "+79991230000",
            'data-mask': "+7(999)9999999",
        }),
    )
    delivery = forms.ChoiceField(
        choices=Orders.Delivery.choices[1:],
        widget=forms.RadioSelect(attrs={
            'class': "toggle-box",
            'id': "delivery",
            'name': "delivery",
            'type': "radio",
            'checked': "checked"
        }),
    )
    payment = forms.ChoiceField(
        choices=Orders.Payment.choices[1:],
        widget=forms.RadioSelect(attrs={
            'class': "toggle-box",
            'id': "payment",
            'name': "payment",
            'type': "radio",
        }),
    )
    city = forms.CharField(max_length=100, label='Город', help_text=_('Город проживания'))
    address = forms.CharField(max_length=200, label='Адрес', help_text=_('Адрес доставки'))
    email = forms.EmailField(max_length=80, label='Почта', help_text=_('Почта'))

    def clean_phone(self):
        """"
        Функция для очистки номера проверки его на уникальность и приведения к int
        """
        phone_str = self.cleaned_data['phone']
        chars_to_remove = ['(', ')']
        for char in chars_to_remove:
            phone_str = phone_str.replace(char, '')
        phone = phone_str[2:]
        return phone

    class Meta:
        model = Profile
        fields = [
            'name', 'phone', 'city', 'address',
            'delivery', 'payment',
        ]


class RegisterForm(UserCreationForm):
    """
    Класс формы для регистрации пользователя
    """

    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={'class': 'form-input'}))
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    password2 = forms.CharField(label='Повтор пароля', widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    phone = forms.CharField(
        max_length=20,
        label='Телефон',
        widget=forms.TextInput(attrs={
            'class': "form-input",
            'id': "phone",
            'name': "phone",
            'type': "text",
            'placeholder': "+79991230000",
        }),
    )

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if Profile.objects.filter(phone=phone).exists():
            raise forms.ValidationError(_("Такой телефон уже существует"))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(_("Такой логин уже существует"))

        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_("Данный email уже существует."))

    def clean_password2(self):
        passw1 = self.cleaned_data['password1']
        passw2 = self.cleaned_data['password2']
        if passw1 != passw2:
            raise forms.ValidationError(_("Пароли не совпадают"))
        if len(passw1) < 6:
            raise forms.ValidationError(_("Пароль должен содержать не менее 6 символов"))

    class Meta:
        model = User
        fields = ('username', 'phone', 'email', 'password1', 'password2')


class SearchForm(forms.ModelForm):
    name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={
            'class': 'search-input',
            'id': 'query',
            'name': 'query',
            'placeholder': 'NVIDIA GeForce RTX 3060',
        })
    )

    class Meta:
        model = Product
        fields = ['name',]


class PaymentForm(forms.Form):
    bill = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input Payment-bill',
            'id': 'numero1',
            'name': 'numero1',
            'type': 'text',
            'placeholder': '9999 9999',
            'data-mask': "9999 9999",
            'data-validate': "require pay",
        })
    )


class JSONImportForm(forms.Form):
    """
    Вьюшка импорта JSON файлов
    """

    json_file = MultiFileField(label=_('json_file'), min_num=1, max_num=10)
    email = forms.EmailField(label=_('email'))
