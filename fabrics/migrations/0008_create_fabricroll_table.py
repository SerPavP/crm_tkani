# Generated manually on 2025-07-25 14:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fabrics', '0007_alter_fabric_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='FabricRoll',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('width_meters', models.DecimalField(decimal_places=2, help_text='Уникальный штрих-код рулона', max_digits=8, verbose_name='Ширина рулона (м)')),
                ('barcode', models.CharField(help_text='Уникальный штрих-код рулона', max_length=100, unique=True, verbose_name='Штрих-код')),
                ('is_active', models.BooleanField(default=True, help_text='Рулон активен (не списан со склада)', verbose_name='Активен')),
                ('created_by_admin', models.BooleanField(default=False, help_text='Рулон создан через интерфейс администратора/бухгалтера', verbose_name='Создан администратором')),
                ('notes', models.TextField(blank=True, help_text='Дополнительная информация о клиенте', verbose_name='Примечания')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('fabric_color', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fabric_rolls_from_fabrics', to='fabrics.fabriccolor', verbose_name='Цвет ткани')),
            ],
            options={
                'verbose_name': 'Рулон ткани',
                'verbose_name_plural': 'Рулоны тканей',
                'ordering': ['-created_at'],
            },
        ),
    ] 