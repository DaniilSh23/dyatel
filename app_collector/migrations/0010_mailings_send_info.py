# Generated by Django 4.1.5 on 2023-03-01 12:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_collector', '0009_rename_datetime_feedback_send_datetime'),
    ]

    operations = [
        migrations.AddField(
            model_name='mailings',
            name='send_info',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Информация об отправке'),
        ),
    ]
