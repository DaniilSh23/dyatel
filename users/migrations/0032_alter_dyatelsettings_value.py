# Generated by Django 4.1.5 on 2023-04-11 13:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0031_profile_agreement_accepted'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dyatelsettings',
            name='value',
            field=models.TextField(max_length=100000, verbose_name='Значение'),
        ),
    ]