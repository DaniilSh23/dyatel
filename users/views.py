import os
import random
import string
import uuid

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.contrib import messages
from django.urls import reverse_lazy
from loguru import logger
# Импорты для работы с GreenApi (WhatsApp)
from whatsapp_api_client_python import API
from whatsapp_api_client_python.response import Response

from app_collector.forms import DfltMsgForm, SendFeedbackForm
from collector import settings
from collector.settings import RBKASSA_MERCHANT_LOGIN, RBKASSA_PASSWORD_1, RBKASSA_PASSWORD_2
from users.models import Profile, DyatelSettings, Transaction, PaymentsInvoices
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.views import View

from users.forms import AuthForm, InputTelegramPhoneForm, InputTelegramCodeForm, InputTelegramTwoFactorPassForm, \
    RegistrationForm, ChangeCompanyNameForm, ChangePasswordForm, ConnectWhatsAppForm, PhoneVerificationForm, \
    ReplenishmentForm
from users.tlg_auth import init_tlg_client, confirm_code, check_2fa_pass
from users.utils import send_sms, check_sms_code, generate_payment_link, result_payment


def login_view(request):
    """
    Вьюшка для страницы авторизации на сайте.
    """
    if request.method == 'POST':  # Для POST пытаемся аутентифицировать пользователя
        auth_form = AuthForm(request.POST)
        if auth_form.is_valid():
            username = auth_form.cleaned_data['username']
            password = auth_form.cleaned_data['password']
            # Функция для проверки пары логин-пароль. Вернёт объект пользователя или None
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    login(request, user)  # Логин, что означает создание сессии для пользователя
                    return redirect('/mailing/')  # сперва нужно указать корень /, иначе ищет путь в этом приложении
                else:
                    auth_form.add_error('__all__', 'Ошибка. Учётная запись не активна!')
            else:
                auth_form.add_error('__all__', 'Ошибка. Неверная пара логин-пароль!')
    else:  # Для всех остальных запросов
        if not request.user.is_anonymous:  # Если пользователь НЕ анонимный(незалогинен)
            return redirect(to='/mailing/')  # Редиректим его на страницу рассылки
        # Всё, что ниже надо прям так оставить, чтобы при неверной паре логин-пароль, снова форма входа прилетала
        auth_form = AuthForm()
    context = {
        'form': auth_form,
    }
    return render(request, template_name='login_collector.html', context=context)


def logout_view(request):
    """
    Вьюшка для логаута пользователя.
    """
    # Код вьюшки удалён из соображений приватности кода проекта


class RegistrationView(View):
    """
    Вьюшка для страницы регистрации.
    """

    def get(self, request, format=None):
        """
        GET - запрос. Отдаём страничку и форму для регистрации.
        """
        reg_form = RegistrationForm()
        context = {
            'reg_form': reg_form,
        }
        return render(request=request, template_name='registration.html', context=context)

    def post(self, request, format=None):
        """
        POST - запрос. Принимаем данные для регистрации, проверяем их валидность, регистрируем или нет.
        """
        reg_form = RegistrationForm(request.POST)
        if reg_form.is_valid():
            username = reg_form.cleaned_data.get("username")
            password1 = reg_form.cleaned_data.get("password1")
            password2 = reg_form.cleaned_data.get("password2")
            company_name = reg_form.cleaned_data.get("company_name")
            if password1 == password2:  # Проверка совпадают ли пароли
                if len(User.objects.filter(username=username)) == 0:  # Проверка зарегистрирован ли такой username
                    user_obj = User.objects.create_user(username=username, password=password1)

                    # Генерируем уникальный токен
                    raw_token = ''.join([str(uuid.uuid4()), str(user_obj.id)])  # Генерим токен, подмешивая ID юзера
                    symbols_str = ''.join([string.ascii_letters, string.digits])  # Собираем вместе буквы и цифры
                    for _ in range(50 - len(raw_token)):  # Добавляем к токену рандомные символы до длины в 50
                        raw_token = ''.join([raw_token, random.choice(symbols_str)])

                    try:
                        bonus = DyatelSettings.objects.get(key='reg_bonus').value
                        # Записываем транзакцию о пополнении стартовым бонусом
                        Transaction.objects.create(
                            user=user_obj,
                            transaction_type='replenishment',
                            amount=float(bonus),
                            description=f'Стартовый бонус ({bonus} руб.)'
                        )

                    except Exception as error:
                        logger.warning(f'В настройках не установлено значение reg_bonus. '
                                       f'Текст ошибки при попытке его получить: {error}')
                        bonus = 0

                    profile_rslt = Profile.objects.get(user=user_obj)
                    profile_rslt.company_name = company_name
                    profile_rslt.api_token_for_1c = raw_token
                    profile_rslt.balance = float(profile_rslt.balance) + float(bonus)
                    profile_rslt.save()

                    # Аутентифицируем и логинем пользователя
                    user = authenticate(username=username, password=password1)
                    login(request, user)
                    return redirect(to='/mailing/?visit=first')  # Редиректим на рассылки
                else:
                    reg_form.add_error('username', error='Пользователь с таким username уже существует.')
            else:
                reg_form.add_error('password2', error='Пароли не совпадают!')
        context = {
            'reg_form': reg_form,
        }
        return render(request=request, template_name='registration.html', context=context)


class ChangePasswordView(View):
    def get(self, request, format=None):
        if request.user.is_anonymous:  # Если пользователь анонимный(незалогинен)
            return redirect(to='/users/login/')

        context = {
            'change_pass_form': ChangePasswordForm(user=request.user)
        }
        return render(request, 'change_password.html', context=context)

    def post(self, request, format=None):
        # Код вьюшки удалён из соображений приватности кода проекта
        return render(request, 'change_password.html', context=context)


class TelegramAuthGetPhone(View):
    """
    Вьюшка для авторизации в телеграмме, а именно для шага получения номера телефона.
    """

    def get(self, request, format=None):
        """
        Обработка GET запроса. Отдаём страничку ввода номера телефона телеграм.
        """
        # Код вьюшки удалён из соображений приватности кода проекта
        return render(request, 'telegram_phone_input.html', context=context)

    def post(self, request, format=None):
        """
        Обработка POST запроса. Получаем номер телефона, высылаем на него код и редиректим на страницу ввода кода
        """
        if request.user.is_anonymous:  # Если пользователь анонимный(незалогинен)
            return redirect(to='/users/login/')
	# Код вьюшки удалён из соображений приватности кода проекта
        return render(request, 'telegram_phone_input.html', context=context)


class TelegramAuthGetCode(View):
    """
    Вьюшка для авторизации в телеграмме, а именно для шага получения кода подтверждения.
    """

    def get(self, request, format=None):  # TODO: это возможно не понадобится
        """
        Обработка GET запроса. Отдаём страничку ввода кода телеграм.
        """
	# Код вьюшки удалён из соображений приватности кода проекта
        return render(request, 'telegram_code_input.html', context=context)

    def post(self, request, format=None):
        """
        Обработка POST запроса. Получаем код, авторизируемся и редиректим либо на успех, либо на ошибку.
        """
        # Код вьюшки удалён из соображений приватности кода проекта
        return render(request, 'telegram_code_input.html', context=context)


class TelegramTwoFactorAuth(View):
    """
    Вьюшка для получения пароля двухфакторной аутентификации.
    """

    def get(self, request, format=None):  # TODO: возможно не понадобится
        """
        Обработка GET-запроса. Получаем пароль 2-ФА.
        """
	# Код вьюшки удалён из соображений приватности кода проекта
        return render(request, 'two_factor_password_input.html', context=context)

    def post(self, request, format=None):
        """
        POST запрос. Проверяем пароль 2-ФА и заканчиваем авторизацию в случае успеха.
        """
	# Код вьюшки удалён из соображений приватности кода проекта
        return render(request, 'two_factor_password_input.html', context=context)


def disable_telegram_account(request):
    """
    Вьюшка для отключения учётной записи Telegram
    """
    if request.user.is_anonymous:  # Если пользователь анонимный(незалогинен)
        return redirect(to='/users/login/')

    if request.method == 'GET':
        profile_obj = Profile.objects.get(user=request.user)
	# Код вьюшки удалён из соображений приватности кода проекта
        return redirect('/users/account/#connected_services')


class AccountView(View):
    """
    Вьюшка для страницы аккаунта
    """

    def get(self, request, format=None):
        if request.user.is_anonymous:  # Если пользователь анонимный(незалогинен)
            return redirect(to='/users/login/')

	# Код вьюшки удалён из соображений приватности кода проекта
        return render(request, 'account.html', context=context)

    def post(self, request, format=None):
	# Код вьюшки удалён из соображений приватности кода проекта
    	return redirect('/users/account/#api_token_for_1c')


class ConnectWhatsAppView(View):
    """
    Вьюшка для обработки запросов при подключении WhatsApp.
    """

    def get(self, request, format=None):
        """
        Обработка GET запроса, отдаём страничку для ввода IdInstance и ApiTokenInstance.
        """
        if request.user.is_anonymous:  # Если пользователь анонимный(незалогинен)
            return redirect(to='/users/login/')

        context = {
            'form': ConnectWhatsAppForm()
        }
        return render(request=request, template_name='connect_whatsapp.html', context=context)

    def post(self, request, format=None):
        """
        Обработчик POST запроса, принимаем данные формы, проверяем валидность и записываем в БД.
        """
        if request.user.is_anonymous:  # Если пользователь анонимный(незалогинен)
            return redirect(to='/users/login/')

	# Код вьюшки удалён из соображений приватности кода проекта
    	return render(request=request, template_name='connect_whatsapp.html', context=context)


def disable_whatsapp_account(request):
    """
    Вьюшка для отключения учётной записи WhatsApp
    """
    if request.user.is_anonymous:  # Если пользователь анонимный(незалогинен)
        return redirect(to='/users/login/')

    # Код вьюшки удалён из соображений приватности кода проекта
    return redirect('/users/account/#connected_services')


def choose_mailing_channel_view(request):
    """
    Вьюшка для обработки запроса по выбору канала для рассылки: WhatsApp или Telegram.
    """
    # Код вьюшки удалён из соображений приватности кода проекта
    return redirect(to='/users/account/#connected_services')


class WalletView(View):
    """
    Вьюшка для страницы кошелька
    """

    def get(self, request, format=None, page_numb=1):
	# Код вьюшки удалён из соображений приватности кода проекта
        return render(request, 'wallet.html', context=context)


class ReplenishmentBalanceView(View):
    """
    Вьюшка для действий по пополнению баланса.
    """
    def get(self, request):
        """
        GET запрос будет отправлен сервисом Robokassa для информирования об успешной оплате счёта клиентом.
        """
	# Код вьюшки удалён из соображений приватности кода проекта
	return HttpResponse(content=answer_to_kassa, status=200)

    def post(self, request):
        """
        На POST запрос создаём платёж в робокассе и редиректим на ссылку оплаты юзера.
        """
	# Код вьюшки удалён из соображений приватности кода проекта
        return HttpResponse(status=400, content=f'Неверное значение для пополнение баланса. '
                                                f'Передано: {request.POST.get("replenishment_amount")}')




def service_in_dev_view(request: HttpRequest) -> HttpResponse:
    """
    Вьюшка для всех функций, которые ещё в разработке
    """
    # Код вьюшки удалён из соображений приватности кода проекта
    return render(request=request, template_name='service_in_dev.html', context=context)


class PhoneVerificationView(View):  # TODO: phone_verification.html - надо сделать, ещё не готово.
    # TODO: Так же добавить запись данных в модель SMSCode.
    def get(self, request):
        form = PhoneVerificationForm()
        context = {
            'form': form,
            'code_input': False,  # Если False, то поле для ввода кода будет спрятано
        }
        return render(request=request, template_name='phone_verification.html', context=context)

    def post(self, request):
        form = PhoneVerificationForm(request.POST)
        if form.is_valid():
            send_rslt = send_sms(phone_number=form.cleaned_data.get('phone_number'),
                                 code=''.join(random.choices(string.digits, k=4)))
            if send_rslt:
                messages.success(request,
                                 f'Сообщение с кодом отправлено на номер: {form.cleaned_data.get("phone_number")}')
            else:
                messages.error(
                    request,
                    f'Не удалось отправить сообщение с кодом на номер: {form.cleaned_data.get("phone_number")}'
                )
            context = {
                'form': form,
                'code_input': True,     # Если True, то поле для ввода номера будет только для чтения
            }
            return render(request=request, template_name='phone_verification.html', context=context)
        else:
            messages.warning(request, 'Неверный формат номера телефона.')
            context = {
                'form': form,
                'code_input': False,     # Если False, то поле для ввода кода будет спрятано
            }
            return render(request=request, template_name='phone_verification.html', context=context)


class CheckCodeView(View):  # TODO: добавить действия с модель SMSCode и обработку успешного подтверждения номера
    """
    Вьюшка для проверки кода подтверждения.
    """
    def post(self, request):
        form = PhoneVerificationForm(request.POST)
        if form.is_valid():
            # Проверяем правильно ли введён код
            if check_sms_code(code=form.cleaned_data.get('code'), phone_number=form.cleaned_data.get('phone_number')):
                messages.success(request, f'Номер телефона успешно подтверждён.')
                return redirect(reverse_lazy("app_collector:mailing"))
        else:
            messages.warning(request, f'Код подтверждения - это 4 цифр.')
            context = {
                'form': form,
                'code_input': False,     # Если False, то поле для ввода кода будет спрятано
            }
            return render(request=request, template_name='phone_verification.html', context=context)


def test_view(request):
    return render(request, template_name='accept_phone.html')
