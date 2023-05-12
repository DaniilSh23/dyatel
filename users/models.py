import os
import time

from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete

from collector import settings


class Profile(models.Model):
    """
    Модель профиля пользователя.
    Она дополняет стандартные данные пользователей Джанго и имеет связь 1к1 с дефолтной Джанго моделью User.
    """
    MLNG_CHANNELS_CHOICES = [
        ('tlg', 'Telegram'),
        ('whtsp', 'WhatsApp'),
    ]
    dflt_txt = 'Здравствуйте, {client}!\n' \
               'Вас приветствует {my_comp}.\n' \
               'Напоминаем, что {date} очередной платеж в размере {amount} рублей. Хорошего дня!\n🐦'
    # отношение таблиц БД ОДИН-К-ОДНОМУ
    user = models.OneToOneField(to=User, verbose_name='Пользователь', on_delete=models.CASCADE)
    company_name = models.CharField(verbose_name='Название компании', max_length=254, blank=True, null=True)
    dflt_mlng_txt = models.TextField(verbose_name='Стандартный текст рассылки', max_length=500, default=dflt_txt)
    tlg_session_file = models.FileField(verbose_name='Файл сессии', upload_to='session_files/', blank=True, null=True)
    tlg_acc_info = models.CharField(verbose_name='Инфо о Telegram аккаунте', max_length=200, blank=True, null=True)
    mailing_channel = models.CharField(verbose_name='Мессенджер для рассылки', max_length=50,
                                       choices=MLNG_CHANNELS_CHOICES, default='tlg')
    green_api_id_instance = models.CharField(verbose_name='IdInstance', max_length=200, blank=True, null=False)
    green_api_token_instance = models.CharField(verbose_name='ApiTokenInstance', max_length=200, blank=True, null=False)
    api_token_for_1c = models.CharField(verbose_name='1C API Token', max_length=50, blank=False, null=True)
    balance = models.DecimalField(verbose_name='Баланс', max_digits=10, decimal_places=2, default=0)
    reserved_for_mailing = models.DecimalField(verbose_name='Зарезервировано под рассылку', max_digits=10,
                                               decimal_places=2, default=0)
    agreement_accepted = models.BooleanField(verbose_name='Принятие договора оферты', default=True)

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
        db_table = 'Профили пользователей'

    def __str__(self):
        return f'Профиль пользователя: {self.user}'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Эта функция нужна для поля ОДИН-К-ОДНОМУ.
    Она нужна для сигналов автоматического создания, к стандартной модели User. Сигнал это - post_save.
    """
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Эта функция нужна для поля ОДИН-К-ОДНОМУ.
    Она нужна для сигналов автоматического обновления, к стандартной модели User. Сигнал это - post_save.
    """
    instance.profile.save()


@receiver(pre_delete, sender=Profile)
def delete_session_file(sender, instance, **kwargs):
    """
    Функция, которая получает сигнал при удалении модели Profile и удаляет файл сессии телеграм
    """
    if instance.tlg_session_file:
        file_path_string = os.path.join(settings.MEDIA_ROOT, instance.tlg_session_file.name)
        if os.path.exists(file_path_string):
            os.remove(file_path_string)


class Transaction(models.Model):
    """
    Транзакции.
    """
    TRANSACTION_TYPE_LST = [
        ('replenishment', 'пополнение'),
        ('write-off', 'списание'),
    ]
    user = models.ForeignKey(verbose_name='Пользователь', to=User, on_delete=models.CASCADE)
    transaction_type = models.CharField(verbose_name='Тип транзакции', choices=TRANSACTION_TYPE_LST, max_length=13)
    transaction_datetime = models.DateTimeField(verbose_name='Дата и время транзакции', auto_now_add=True)
    amount = models.DecimalField(verbose_name='Сумма', default=0, max_digits=10, decimal_places=2)
    description = models.TextField(verbose_name='Описание', max_length=250, null=True)

    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
        ordering = ['-id']


class DyatelSettings(models.Model):
    """
    Модель для настроек проекта (хранилище key-value).
    """
    key = models.CharField(verbose_name='Ключ', max_length=100)
    value = models.TextField(verbose_name='Значение', max_length=23000)

    class Meta:
        verbose_name = 'Настройка'
        verbose_name_plural = 'Настройки'
        ordering = ['-id']


class SMSCode(models.Model):
    """
    Модель для хранения инфы о СМС кодах подтверждения.
    """
    phone_number = models.CharField(verbose_name='телефон', max_length=23)
    code = models.CharField(verbose_name='код', max_length=4)
    expired_at = models.FloatField(verbose_name='когда истекает(сек.)', default=time.time() + 60 * 5)
    input_attempts = models.IntegerField(verbose_name='попытки для ввода кода', default=5)
    already_registered = models.BooleanField(verbose_name='Уже зарегистрирован', default=False)

    class Meta:
        verbose_name = 'СМС код'
        verbose_name_plural = 'СМС коды'
        ordering = ['-pk']


class PaymentsInvoices(models.Model):
    """
    Модель для хранения инфы о счетах на оплату.
    """
    user = models.ForeignKey(verbose_name='Пользователь', to=User, on_delete=models.CASCADE)
    amount = models.DecimalField(verbose_name='Сумма', max_digits=10, decimal_places=2)
    description = models.TextField(verbose_name='Описание', max_length=1000)
    payment_url = models.URLField(verbose_name='Ссылка на оплату', max_length=1000, blank=True, null=False)
    pass_1_hash = models.CharField(verbose_name='Хэш из пароля 1', max_length=100, blank=True, null=False)
    is_paid = models.BooleanField(verbose_name='оплачен', default=False)
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Счёт на оплату'
        verbose_name_plural = 'Счета на оплату'
        ordering = ['-pk']
