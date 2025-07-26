# Generated manually on 2025-07-25 13:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('create', 'Создание'), ('update', 'Редактирование'), ('delete', 'Удаление'), ('barcode_create', 'Создание штрих-кода'), ('barcode_scan', 'Сканирование штрих-кода'), ('login', 'Вход в систему'), ('logout', 'Выход из системы')], max_length=20, verbose_name='Действие')),
                ('object_type', models.CharField(max_length=50, verbose_name='Тип объекта')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True, verbose_name='ID объекта')),
                ('description', models.TextField(verbose_name='Описание')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Время')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.user', verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Лог активности',
                'verbose_name_plural': 'Логи активности',
                'ordering': ['-timestamp'],
            },
        ),
    ] 