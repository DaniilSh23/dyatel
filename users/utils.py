"""Тут будут разные функции для тех или иных действий, который я вынес, 
чтобы не перегружать основной код, например views"""

import requests
import hashlib
from urllib import parse
from urllib.parse import urlparse


'''ПЛАТЕЖИ С РОБОКАССОЙ'''


def calculate_signature(*args) -> str:
    """
    Функция для создания хэша в MD5.
    """
    signature_value = ':'.join(str(arg) for arg in args).encode('utf-8')
    return hashlib.md5(signature_value).hexdigest()


def generate_payment_link(
        merchant_login: str,  # Merchant login
        merchant_password_1: str,  # Merchant password
        cost: str,  # Cost of goods, RU, example '123.45'
        number: int,  # Invoice number
        description: str,  # Description of the purchase
        is_test=0,
        robokassa_payment_url='https://auth.robokassa.ru/Merchant/Index.aspx',
) -> tuple:
    """
    Функция для генерации ссылки на оплату, возвращает (ссылка на оплату, хэш с паролем 1)
    """
    signature = calculate_signature(
        merchant_login,
        cost,
        number,
        merchant_password_1
    )
    data = {
        'MerchantLogin': merchant_login,
        'OutSum': str(cost),
        'InvId': number,
        'Description': description,
        'SignatureValue': signature,
        'IsTest': is_test,
        'Encoding': 'utf-8',
    }
    return f'{robokassa_payment_url}?{parse.urlencode(data)}', signature


def check_signature_result(
    order_number: int,  # invoice number
    received_sum: str,  # cost of goods, RU
    received_signature: hex,  # SignatureValue
    password: str  # Merchant password
) -> bool:
    """
    Функция для проверки хэша, который пришёл в запросе, путём самостоятельного расчёта и сравнения.
    """
    signature = calculate_signature(received_sum, order_number, password)
    if signature.lower() == received_signature.lower():
        return True
    return False


def result_payment(merchant_password_2: str, amount, invoice_numb, signature) -> str:
    """
    Функция, которая проверяет запрос об успешной оплате и даёт ответ, если проверка была успешной.
    Возвращает: отформатированный ответ для робокассы
    """
    if check_signature_result(invoice_numb, amount, signature, merchant_password_2):
        return f'OK{invoice_numb}'


'''ПОДТВЕРЖДЕНИЕ ТЕЛЕФОНА ЧЕРЕЗ СМС КОД'''


def send_sms(phone_number, code):
    """
    Отправка СМС с кодом подтверждения через сервис smsc.ru
    """
    smsc_url = 'https://smsc.ru/sys/send.php'
    smsc_login = 'ваш логин на smsc.ru'
    smsc_password = 'ваш пароль на smsc.ru'
    smsc_sender = 'ваш отправитель'

    # Формируем запрос к API сервиса smsc.ru
    response = requests.get(smsc_url, params={
        'login': smsc_login,
        'psw': smsc_password,
        'phones': phone_number,
        'sender': smsc_sender,
        'mes': f'Код подтверждения: {code}',
        'fmt': 3  # формат ответа в виде JSON
    })

    # Возвращаем True, если сообщение было успешно отправлено
    return response.json()['cnt'] == 1


def check_sms_code(code, phone_number):     # TODO: а надо ли это, если код сохраняем у себя?...
    """
    Функция для сверки отправленного кода через smsc.ru и введённого юзером.
    """
    url = 'https://smsc.ru/sys/check.php'
    params = {
        'login': 'Ваш_логин',
        'psw': 'Ваш_пароль',
        'phones': phone_number,
        'code': code
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        if response.text == 'OK':
            return True
    return False
