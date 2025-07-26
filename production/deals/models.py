from django.db import models
from django.db.models import Sum
from clients.models import Client
from fabrics.models import FabricColor


class Deal(models.Model):
    """
    Модель сделки/заказа
    """
    STATUS_CHOICES = [
        ('created', 'Создан'),
        ("pending_payment", "Ожидание оплаты"),
        ('paid', 'Оплачен')
    ]
    
    deal_number = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Номер заказа",
        help_text="Автоматически генерируемый номер заказа"
    )
    client = models.ForeignKey(
        Client, 
        on_delete=models.CASCADE, 
        verbose_name="Клиент"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='created', 
        verbose_name="Статус"
    )
    total_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="Сумма без НДС (₸)",
        null=True, blank=True
    )
    total_with_vat = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="Сумма с НДС (₸)",
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = "Сделка"
        verbose_name_plural = "Сделки"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Заказ {self.deal_number} - {self.client.nickname}"
    
    def save(self, *args, **kwargs):
        if not self.deal_number:
            # Генерация уникального номера заказа
            import datetime
            today = datetime.date.today()
            prefix = f"ORD-{today.strftime('%Y%m%d')}"
            
            # Найти последний номер за сегодня
            last_deal = Deal.objects.filter(
                deal_number__startswith=prefix
            ).order_by('-deal_number').first()
            
            if last_deal:
                last_number = int(last_deal.deal_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.deal_number = f"{prefix}-{new_number:04d}"
        
        super().save(*args, **kwargs)
    
    def update_totals(self):
        """Обновляет общие суммы сделки"""
        from decimal import Decimal
        total = self.dealitem_set.aggregate(total=Sum('total_price'))['total'] or Decimal('0')
        self.total_amount = total
        self.total_with_vat = total * Decimal('1.12')  # НДС 12%
        
    @property
    def total_profit(self):
        """Общая прибыль по сделке (с учетом себестоимости)"""
        from decimal import Decimal
        profit = Decimal('0')
        for item in self.dealitem_set.all():
            item_cost = Decimal(str(item.width_meters)) * Decimal(str(item.fabric_color.fabric.cost_price))
            item_profit = Decimal(str(item.total_price)) - item_cost
            profit += item_profit
        return profit


class DealItem(models.Model):
    """
    Модель позиции заказа
    """
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, verbose_name="Заказ")
    fabric_color = models.ForeignKey(
        FabricColor, 
        on_delete=models.CASCADE, 
        verbose_name="Цвет ткани"
    )
    width_meters = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        verbose_name="Ширина (м)"  # Используется термин "ширина" по требованию заказчика
    )
    price_per_meter = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Цена за метр ширины (₸)"  # Используется термин "ширина" по требованию заказчика
    )
    total_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="Сумма (₸)"
    )
    position_number = models.PositiveIntegerField(verbose_name="Номер позиции")
    
    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказов"
        ordering = ['position_number']
    
    def __str__(self):
        return f"Позиция {self.position_number} - {self.fabric_color}"
    
    def save(self, *args, **kwargs):
        if not self.position_number:
            # Автоматическое присвоение номера позиции
            last_position = DealItem.objects.filter(deal=self.deal).order_by(
                '-position_number'
            ).first()
            if last_position:
                self.position_number = last_position.position_number + 1
            else:
                self.position_number = 1
        # Автоматический расчет суммы позиции
        from decimal import Decimal
        self.total_price = Decimal(str(self.width_meters)) * Decimal(str(self.price_per_meter))
        super().save(*args, **kwargs)
