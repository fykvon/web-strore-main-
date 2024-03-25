from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import Profile


class UserUpdateForm(forms.ModelForm):
    """
    Форма обновления данных пользователя
    """
    password_placeholder = _("Тут можно изменить пароль")
    password2_placeholder = _("Введите пароль повторно")
    name = forms.CharField(
        label='name',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': "form-input",
            'id': "name",
            'name': "name",
            'type': "text",
            'data-validate': "require"
        })
    )
    email = forms.EmailField(
        label='email',
        widget=forms.EmailInput(attrs={
            'class': "form-input",
            'id': "email",
            'name': "email",
            'type': "email",
            'data-validate': "require",
            'placeholder': "send@test.test"
        }),
    )
    password = forms.CharField(
        label='password',
        min_length=8,
        max_length=50,
        widget=forms.PasswordInput(attrs={
            'class': "form-input",
            'id': "password",
            'name': "password",
            'type': "password",
            'placeholder': password_placeholder
        })
    )
    password_2 = forms.CharField(
        label='password_2',
        min_length=8,
        max_length=50,
        widget=forms.PasswordInput(attrs={
            'class': "form-input",
            'id': "password_2",
            'name': "password_2",
            'type': "password",
            'placeholder': password2_placeholder
        })
    )

    def clean_email(self):
        """
        Проверка email на уникальность
        """
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(username=self.instance.username).exists():
            raise forms.ValidationError(_('Email адрес должен быть уникальным'))
        return email

    def clean_password_2(self):
        passw1 = self.cleaned_data['password']
        passw2 = self.cleaned_data['password_2']
        if passw1 != passw2:
            raise forms.ValidationError(_('Пароли не совпадают'))
        if len(passw1) < 6:
            raise forms.ValidationError(_('Пароль должен содержать не менее 6 символов'))

    class Meta:
        model = User
        fields = ('name', 'email', 'password', 'password_2')


class ProfileUpdateForm(forms.ModelForm):
    """
    Форма обновления данных профиля пользователя
    """
    avatar = forms.ImageField(
        label='avatar',
        required=False,
        widget=forms.FileInput(attrs={
            'class': "Profile-file form-input",
            'id': "avatar",
            'name': "avatar",
            'type': "file",
            'enctype': "multipart/form-data",
            'data-validate': "onlyImgAvatar"
        })
    )
    phone = forms.CharField(
        label='Телефон',
        widget=forms.TextInput(attrs={
            'class': "form-input",
            'id': "phone",
            'name': "phone",
            'type': "text",
            'placeholder': "+7(999)9999999",
            'data-mask': "+7(999)9999999",

        })
    )

    def clean_avatar(self):
        """"
       Функция, ограничивающая размер загружаемой avatar
       """
        image = self.cleaned_data.get('avatar', False)
        if image:
            if image.size > 2.5 * 1024 * 1024:
                raise forms.ValidationError(_('Размер изображения слишком большой ( > 2.5mb )'))
            return image
        else:
            raise forms.ValidationError(_('Не удалось прочитать загруженное изображение'))

    def clean_phone(self):
        """"
        Функция для очистки номера проверки его на уникальность и приведения к int
        """
        phone_str = self.cleaned_data['phone']
        chars_to_remove = ['(', ')']
        for char in chars_to_remove:
            phone_str = phone_str.replace(char, '')
        phone = phone_str[2:]
        if phone and Profile.objects.filter(phone=phone).exclude(id=self.instance.id).exists():
            raise forms.ValidationError(_('Телефон должен быть уникальным'))
        return phone

    class Meta:
        model = Profile
        fields = ('avatar', 'phone')


class RegisterForm(forms.ModelForm):
    """
    Форма регистрации
    """

    username = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'user-input',
            'id': 'name',
            'name': 'name',
            'placeholder': _('Имя'),
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'user-input',
            'id': 'email',
            'name': 'email',
            'placeholder': 'E-mail',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'user-input',
            'id': 'password',
            'name': 'pass',
            'placeholder': _('Пароль'),
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'user-input',
            'id': 'password2',
            'name': 'pass',
            'placeholder': _('Повтор Пароля'),
        })
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(_("Такой логин уже существует"))

        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_("Данный email уже существует."))

        return email

    def clean_password2(self):
        passw1 = self.cleaned_data['password']
        passw2 = self.cleaned_data['password2']
        if passw1 != passw2:
            raise forms.ValidationError(_("Пароли не совпадают"))
        if len(passw1) < 6:
            raise forms.ValidationError(_("Пароль должен содержать не менее 6 символов"))

    class Meta:
        model = User
        fields = ['username', 'email', 'password']


class LoginForm(forms.Form):
    """
    Форма авторизации
    """

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'user-input',
            'id': 'login',
            'name': 'email',
            'placeholder': 'E-mail',
        })
    )
    password = forms.CharField(
        max_length=20,
        widget=forms.PasswordInput(attrs={
            'class': 'user-input',
            'id': 'password',
            'name': 'pass',
            'placeholder': '*********',
        })
    )
