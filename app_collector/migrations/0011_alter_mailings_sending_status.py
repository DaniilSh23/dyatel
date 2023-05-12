# Generated by Django 4.1.5 on 2023-03-22 08:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_collector', '0010_mailings_send_info'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mailings',
            name='sending_status',
            field=models.CharField(choices=[('queued', 'в очереди'), ('cmplt', 'отправлено'), ('cncld', 'не отправлено'), ('dlvrd', 'доставлено'), ('read', 'прочитано')], default='queued', max_length=6, verbose_name='Статус отправки'),
        ),
    ]