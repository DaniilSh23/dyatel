# Generated by Django 4.1.5 on 2023-04-11 13:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0030_alter_transaction_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='agreement_accepted',
            field=models.BooleanField(default=True, verbose_name='Принятие договора оферты'),
        ),
    ]
