# Generated by Django 4.1.5 on 2023-02-03 19:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_remove_profile_path_to_tlg_session_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='path_to_tlg_session_file',
            field=models.FilePathField(null=True, verbose_name='Путь к файлу сессии'),
        ),
    ]
