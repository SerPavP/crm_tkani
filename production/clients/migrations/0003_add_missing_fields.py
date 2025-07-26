# Generated manually on 2025-07-25 12:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0002_remove_client_description_client_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='email',
            field=models.EmailField(blank=True, help_text='Электронная почта клиента', max_length=255, null=True, verbose_name='Email'),
        ),
        migrations.AddField(
            model_name='client',
            name='address',
            field=models.CharField(blank=True, help_text='Физический адрес клиента', max_length=255, null=True, verbose_name='Адрес'),
        ),
    ] 