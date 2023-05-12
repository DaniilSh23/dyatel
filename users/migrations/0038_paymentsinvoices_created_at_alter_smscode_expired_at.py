# Generated by Django 4.1.5 on 2023-04-18 11:50

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0037_remove_paymentsinvoices_pass_2_hash_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentsinvoices',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Дата создания'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='smscode',
            name='expired_at',
            field=models.FloatField(default=1681818927.3307405, verbose_name='когда истекает(сек.)'),
        ),
    ]
