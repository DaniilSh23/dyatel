# Generated by Django 4.1.5 on 2023-02-16 07:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_alter_profile_dflt_mlng_txt'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='company_name',
            field=models.CharField(blank=True, max_length=254, null=True, verbose_name='Название компании'),
        ),
    ]