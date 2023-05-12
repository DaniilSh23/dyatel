from django import forms
from django.contrib.auth.forms import PasswordChangeForm


class AuthForm(forms.Form):
    # Вот так мы указываем все стили и другие аттрибуты, которые уже есть в вёрстке страницы.
    username = forms.CharField(min_length=3, widget=forms.TextInput(attrs={
        "id": "signin-email",  # в тэге label для этого поля надо изменить аттрибут for="{form.username.id_for_label}"
        "name": "signin-email",
        "type": "text",
        "class": "form-control signin-email",
        "placeholder": "Введите логин",
        "required": "required"
    }))
    # здесь мы указываем виджет, который нужен для поля паролей
    password = forms.CharField(min_length=5, widget=forms.PasswordInput(attrs={
        "id": "signin-password",  # аналогично как и для username (for="{form.username.id_for_label}")
        "name": "signin-password",
        "type": "password",
        "class": "form-control signin-password",
        "placeholder": "Введите пароль",
        "required": "required",
    }))


class RegistrationForm(forms.Form):
    company_name = forms.CharField(max_length=254, help_text='Введите название вашей компании.', widget=forms.TextInput(
        attrs={
            "id": "signup-password",
            "name": "company_name",
            "type": "text",
            "class": "form-control signup-name",
            "placeholder": "Название компании",
            "required": "required",
        }))
    username = forms.CharField(min_length=3, max_length=50, help_text='Введите логин', widget=forms.TextInput(
        attrs={
            "id": "signup-name",
            "name": "username",
            "type": "text",
            "class": "form-control signup-name",
            "placeholder": "Логин",
            "required": "required",
        }))
    password1 = forms.CharField(min_length=5, max_length=50, help_text='Введите пароль', widget=forms.PasswordInput(
        attrs={
            "id": "signup-password",
            "name": "password1",
            "type": "password",
            "class": "form-control signup-password",
            "placeholder": "Пароль",
            "required": "required",
        }))
    password2 = forms.CharField(min_length=5, max_length=50, help_text='Повторите пароль', widget=forms.PasswordInput(
        attrs={
            "id": "signup-password2",
            "name": "password2",
            "type": "password",
            "class": "form-control signup-password",
            "placeholder": "Повторите пароль",
            "required": "required",
        }))


class ChangePasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Атрибуты для поля старого пароля
        self.fields['old_password'].widget.attrs['id'] = 'old_password'
        self.fields['old_password'].widget.attrs['name'] = 'old_password'
        self.fields['old_password'].widget.attrs['type'] = 'password'
        self.fields['old_password'].widget.attrs['class'] = 'form-control signup-password'
        self.fields['old_password'].widget.attrs['placeholder'] = 'Старый пароль'
        self.fields['old_password'].widget.attrs['required'] = 'required'
        # Атрибуты для поля нового пароля 1
        self.fields['new_password1'].widget.attrs['id'] = 'new_password1'
        self.fields['new_password1'].widget.attrs['name'] = 'new_password1'
        self.fields['new_password1'].widget.attrs['type'] = 'password'
        self.fields['new_password1'].widget.attrs['class'] = 'form-control signup-password'
        self.fields['new_password1'].widget.attrs['placeholder'] = 'Новый пароль'
        self.fields['new_password1'].widget.attrs['required'] = 'required'
        # Атрибуты для поля нового пароля 2
        self.fields['new_password2'].widget.attrs['id'] = 'new_password2'
        self.fields['new_password2'].widget.attrs['name'] = 'new_password2'
        self.fields['new_password2'].widget.attrs['type'] = 'password'
        self.fields['new_password2'].widget.attrs['class'] = 'form-control signup-password'
        self.fields['new_password2'].widget.attrs['placeholder'] = 'Повторите новый пароль'
        self.fields['new_password2'].widget.attrs['required'] = 'required'


'''ФОРМЫ ДЛЯ АВТОРИЗАЦИИ ТЕЛЕГРАММ АККАУНТА(начало)'''


class InputTelegramPhoneForm(forms.Form):
    """
    Форма для ввода номера телефона, привязанного к телеграмм.
    """
    phone_number = forms.CharField(widget=forms.TextInput(attrs={
        "type": "tel",
        "placeholder": "Введите номер телефона"
    }))


class InputTelegramCodeForm(forms.Form):
    """
    Форма для ввода кода подтверждения, присланного телеграмом.
    """
    code = forms.CharField(min_length=5, max_length=5, widget=forms.TextInput(attrs={
        "type": "number",
        "placeholder": "Введите код подтверждения"
    }))


class InputTelegramTwoFactorPassForm(forms.Form):
    """
    Форма для ввода пароля двух факторной аутентификации.
    """
    two_fa_pass = forms.CharField(widget=forms.PasswordInput(attrs={
        "type": "password",
        "placeholder": "Введите пароль"
    }))


'''ФОРМЫ ДЛЯ АВТОРИЗАЦИИ ТЕЛЕГРАММ АККАУНТА(конец)'''


class ChangeCompanyNameForm(forms.Form):
    """
    Форма для изменения названия компании
    """
    company_name = forms.CharField(widget=forms.TextInput(attrs={
        'type': 'text',
        'class': 'form-control',
        'id': 'comp_name_field',
        'required': 'required',
    }))


class ConnectWhatsAppForm(forms.Form):
    """
    Форма для подключения WhatsApp. Запрашивает IdInstance и ApiTokenInstance из сервиса GREEN-API.
    """
    id_instance = forms.CharField(max_length=200, widget=forms.TextInput(attrs={
        'type': 'text',
        'id': 'id_instance',
        'placeholder': 'Введите IdInstance',
        'required': 'required',
    }))
    api_token_instance = forms.CharField(max_length=200, widget=forms.TextInput(attrs={
        'type': 'text',
        'id': 'api_token_instance',
        'placeholder': 'Введите ApiTokenInstance',
        'required': 'required',
    }))


class ChoiceMailingChannelForm(forms.Form):
    """
    Форма для выбора мессенджера для рассылки.
    """
    MLNG_CHANNELS_CHOICES = (
        ('tlg', 'Telegram'),
        ('whtsp', 'WhatsApp'),
    )
    choice_messanger = forms.ChoiceField(choices=MLNG_CHANNELS_CHOICES, widget=forms.RadioSelect(attrs={
        # 'class': 'form-check-input',
        'type': 'radio',
    }))


class PhoneVerificationForm(forms.Form):
    """
    Форма для верификации номера телефона.
    """
    phone_number = forms.CharField(max_length=25)
    code = forms.CharField(max_length=4)


class ReplenishmentForm(forms.Form):
    """
    Форма для пополнения баланса на какую-либо сумму.
    """
    replenishment_amount = forms.DecimalField(max_digits=10, decimal_places=2)
