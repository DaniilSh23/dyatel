import os

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from collector import settings


class Clients(models.Model):
    """
    Модель для таблицы клиентов пользователей сайта
    """
    user = models.ForeignKey(verbose_name='Пользователь сайта', to=User, on_delete=models.CASCADE)
    client_name = models.CharField(verbose_name='Клиент', max_length=100)
    telephone_or_username = models.CharField(verbose_name='Телефон/@username', max_length=100)
    custom_mlng_txt = models.TextField(verbose_name='Пользовательский текст рассылки',
                                       max_length=500, blank=True, null=True)
    amount_of_pmnt = models.DecimalField(verbose_name='Сумма платежа', decimal_places=2, max_digits=30)
    pmnt_date = models.DateTimeField(verbose_name='Дата и время платежа')

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        db_table = 'Клиенты пользователей сайта'
        ordering = ['-pmnt_date']

    def __str__(self):
        return f'Клиент {self.client_name}'


def generate_path_to_clients_files(instance: "ClientsFiles", filename: str) -> str:
    """
    Функция для генерации пути к файлам клиента.
    """
    return 'clients_files/{filename}'.format(
        filename=filename,
    )


class ClientsFiles(models.Model):
    """
    Модель для файлов таблицы Clients
    """
    client = models.ForeignKey(verbose_name='Объект клиента', to=Clients, on_delete=models.CASCADE,
                               related_name='clients_file')
    file = models.FileField(verbose_name='Файл', upload_to=generate_path_to_clients_files)
    file_size = models.FloatField(verbose_name='Размер файла', default=0)
    file_name = models.CharField(verbose_name='Имя файла', max_length=100)

    def __str__(self):
        return f'Файл клиента {self.client}'

    class Meta:
        verbose_name = 'Файл клиента'
        verbose_name_plural = 'Файлы клиента'
        ordering = ['-id']


@receiver(pre_delete, sender=ClientsFiles)
def delete_session_file(sender, instance, **kwargs):
    """
    Функция, которая получает сигнал при удалении модели Profile и удаляет файл сессии телеграм
    """
    if instance.file:
        file_path_string = os.path.join(settings.MEDIA_ROOT, instance.file.name)
        if os.path.exists(file_path_string):
            os.remove(file_path_string)     # Удаляем файл


class Mailings(models.Model):
    """
    Модель для таблицы рассылок пользователей сайта
    """
    LIST_FOR_CHOICES = [
        ('queued', 'в очереди'),
        ('cmplt', 'отправлено'),
        ('cncld', 'не отправлено'),
        ('dlvrd', 'доставлено'),
        ('read', 'прочитано'),
    ]
    client = models.ForeignKey(verbose_name='Клиент', to=Clients, on_delete=models.CASCADE)
    # В mlng_txt записывается текст рассылки. Либо кастомный, либо дефолтный.
    mlng_txt = models.TextField(verbose_name='Текст рассылки', max_length=500)
    sent_datetime = models.DateTimeField(verbose_name='Дата и время отправки', blank=True, null=True)
    sending_status = models.CharField(verbose_name='Статус отправки', choices=LIST_FOR_CHOICES,
                                      default='queued', max_length=6)
    send_info = models.CharField(verbose_name='Информация об отправке', max_length=200, blank=True, null=True)

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
        db_table = 'Рассылки пользователей сайта'
        ordering = ['-id']

    def __str__(self):
        return f'Рассылка клиенту {self.client}'


class Feedback(models.Model):
    """
    Модель для таблицы обратной связи от пользователей сайта.
    """
    user = models.ForeignKey(verbose_name='Пользователь', to=User, on_delete=models.CASCADE)
    feedback_text = models.TextField(verbose_name='Текст фидбэка', max_length=1000)
    send_datetime = models.DateTimeField(verbose_name='Дата и время фидбэка', auto_now_add=True)

    class Meta:
        verbose_name = 'Фидбэк пользователя'
        verbose_name_plural = 'Фидбэки пользователей'
        ordering = ['-id']

    def __str__(self):
        return f'Фидбэк пользователя {self.user}'
