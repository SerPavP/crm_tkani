from django.db import models

class SystemSettings(models.Model):
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=12.00, verbose_name="Ставка НДС (%)")
    markup_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=20.00, verbose_name="Автоматическая наценка (%)")

    class Meta:
        verbose_name = "Настройки системы"
        verbose_name_plural = "Настройки системы"

    def __str__(self):
        return "Настройки системы"

    def save(self, *args, **kwargs):
        # Гарантируем, что существует только одна запись настроек
        if not self.pk and SystemSettings.objects.exists():
            raise Exception("Может существовать только одна запись SystemSettings")
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


