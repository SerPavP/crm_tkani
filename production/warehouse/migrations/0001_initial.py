# Generated by Django 5.0.4 on 2025-07-23 08:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('fabrics', '0002_alter_fabricroll_fabric_color'),
    ]

    operations = [
        migrations.CreateModel(
            name='FabricRoll',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('barcode', models.CharField(max_length=100, unique=True, verbose_name='Штрих-код рулона')),
                ('width_meters', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Ширина рулона (м)')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активный')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('fabric_color', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fabric_rolls_from_warehouse', to='fabrics.fabriccolor', verbose_name='Цвет ткани')),
            ],
            options={
                'verbose_name': 'Рулон ткани',
                'verbose_name_plural': 'Рулоны ткани',
                'ordering': ['-created_at'],
            },
        ),
    ]
