from django.db import models


class Client(models.Model):
    """
    Модель клиента
    """
    nickname = models.CharField(
        max_length=200, 
        verbose_name="Никнейм / Название компании",
        help_text="Краткое название или никнейм клиента"
    )
    full_name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name="Полное имя / ФИО контактного лица",
        help_text="Полное имя клиента или ФИО контактного лица"
    )
    phone = models.CharField(
        max_length=20, 
        verbose_name="Номер телефона",
        help_text="Контактный номер телефона"
    )
    email = models.EmailField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name="Email",
        help_text="Электронная почта клиента"
    )
    address = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name="Адрес",
        help_text="Физический адрес клиента"
    )
    notes = models.TextField(
        blank=True, 
        verbose_name="Примечания",
        help_text="Дополнительная информация о клиенте"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        ordering = ['nickname']
    
    def __str__(self):
        return f"{self.nickname} ({self.phone})"
    
    @property
    def total_orders_amount(self):
        """Общая сумма всех заказов клиента"""
        from deals.models import Deal
        total = self.deal_set.aggregate(
            total=models.Sum('total_with_vat')
        )['total']
        return total or 0
    
    @property
    def orders_count(self):
        """Количество заказов клиента"""
        return self.deal_set.count()
    
    @property
    def last_order_date(self):
        """Дата последнего заказа"""
        last_deal = self.deal_set.order_by('-created_at').first()
        return last_deal.created_at if last_deal else None

