# Generated by Django 4.1.5 on 2023-03-29 08:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0023_dyatelsettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='balance',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Баланс'),
        ),
    ]
