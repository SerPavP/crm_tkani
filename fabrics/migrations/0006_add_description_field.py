# Generated manually on 2025-07-25 13:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fabrics', '0005_fabric_selling_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='fabric',
            name='description',
            field=models.TextField(blank=True, help_text='Описание ткани', verbose_name='Описание'),
        ),
    ] 