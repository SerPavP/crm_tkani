from django.db import models


class Fabric(models.Model):
    """
    Модель ткани
    """
    name = models.CharField(max_length=200, verbose_name="Название ткани")
    description = models.TextField(
        blank=True, 
        verbose_name="Описание",
        help_text="Дополнительное описание ткани"
    )
    cost_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Себестоимость",
        help_text="Себестоимость ткани (применяется ко всем цветам)"
    )
    selling_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Цена продажи",
        help_text="Цена, по которой ткань продается клиентам",
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = "Ткань"
        verbose_name_plural = "Ткани"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def total_width_meters(self):
        """Общее количество метров всех цветов этой ткани"""
        total = 0
        for color in self.fabriccolor_set.all():
            total += color.total_width_meters
        return total
    
    @property
    def total_width_meters_formatted(self):
        """Отформатированное количество метров (без лишних нулей)"""
        total = self.total_width_meters
        if total == 0:
            return "0м"
        # Убираем лишние нули после запятой
        formatted = f"{total:.2f}".rstrip('0').rstrip('.')
        return f"{formatted}м"

    def save(self, *args, **kwargs):
        # Автоматически рассчитываем цену продажи если не задана
        if not self.selling_price and self.cost_price:
            try:
                from finances.models import SystemSettings
                settings = SystemSettings.load()
                markup = settings.markup_percentage / 100  # Конвертируем проценты в коэффициент
                self.selling_price = self.cost_price * (1 + markup)
            except:
                # Если настройки недоступны, используем наценку 20%
                self.selling_price = self.cost_price * 1.20
        super().save(*args, **kwargs)

    @property
    def sorted_colors(self):
        """Цвета, отсортированные: сначала с рулонами, потом без рулонов, по номеру цвета"""
        
        colors_with_rolls = []
        colors_without_rolls = []
        
        for color in self.fabriccolor_set.all():
            has_rolls = FabricRoll.objects.filter(
                fabric_color=color, 
                is_active=True
            ).exists()
            
            if has_rolls:
                colors_with_rolls.append(color)
            else:
                colors_without_rolls.append(color)
        
        # Сортируем по номеру цвета
        colors_with_rolls.sort(key=lambda x: int(x.color_number) if x.color_number.isdigit() else 9999)
        colors_without_rolls.sort(key=lambda x: int(x.color_number) if x.color_number.isdigit() else 9999)
        
        # Ограничиваем до 5 цветов для списка
        return (colors_with_rolls + colors_without_rolls)[:5]

    @property
    def deals_count(self):
        """Количество сделок, использующих эту ткань"""
        from deals.models import DealItem
        return DealItem.objects.filter(fabric_color__fabric=self).count()


class FabricColor(models.Model):
    """
    Модель цвета ткани
    """
    fabric = models.ForeignKey(Fabric, on_delete=models.CASCADE, verbose_name="Ткань")
    color_name = models.CharField(max_length=100, verbose_name="Название цвета")
    color_number = models.CharField(max_length=50, verbose_name="Номер цвета", blank=True)
    color_hex = models.CharField(
        max_length=7, 
        verbose_name="HEX код цвета",
        help_text="Цвет для визуального отображения (например, #FF0000)",
        default="#CCCCCC"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = "Цвет ткани"
        verbose_name_plural = "Цвета тканей"
        unique_together = ['fabric', 'color_number']
        ordering = ['fabric__name', 'color_number']
    
    def __str__(self):
        return f"{self.fabric.name} - {self.color_name} ({self.color_number})"
    
    @property
    def price_per_meter(self):
        """Цена за метр берется из себестоимости ткани"""
        return self.fabric.cost_price
    
    @property
    def total_width_meters(self):
        """Общее количество метров ширины всех активных рулонов этого цвета"""
        # Используется термин "ширина" по требованию заказчика
        total = FabricRoll.objects.filter(fabric_color=self, is_active=True).aggregate(
            total=models.Sum('width_meters')
        )['total']
        return total or 0
    
    @property
    def total_width_meters_formatted(self):
        """Отформатированное количество метров (без лишних нулей)"""
        total = self.total_width_meters
        if total == 0:
            return "0м"
        # Убираем лишние нули после запятой
        formatted = f"{total:.2f}".rstrip('0').rstrip('.')
        return f"{formatted}м"
    
    @property
    def active_rolls_list(self):
        """Список ширин активных рулонов для отображения"""
        rolls = FabricRoll.objects.filter(fabric_color=self, is_active=True).values_list('width_meters', flat=True)
        return [f"{roll}м" for roll in rolls]
    
    @property
    def active_rolls_simple(self):
        """Список ширин активных рулонов в виде чисел"""
        rolls = FabricRoll.objects.filter(fabric_color=self, is_active=True).values_list('width_meters', flat=True).order_by('width_meters')
        return [str(int(roll)) if roll == int(roll) else str(roll) for roll in rolls]
    
    @property
    def total_value(self):
        """Общая стоимость всех активных рулонов этого цвета"""
        return self.total_width_meters * self.fabric.cost_price
    
    @property
    def active_rolls_count(self):
        """Количество активных рулонов данного цвета"""
        from .models import FabricRoll # Импортируем здесь, чтобы избежать циклической зависимости
        return FabricRoll.objects.filter(fabric_color=self, is_active=True).count()

    def save(self, *args, **kwargs):
        """Автоматическая генерация номера цвета если он не указан"""
        if not self.color_number:
            # Генерируем случайный номер от 100 до 999
            import random
            while True:
                number = random.randint(100, 999)
                if not FabricColor.objects.filter(fabric=self.fabric, color_number=str(number)).exists():
                    self.color_number = str(number)
                    break
        super().save(*args, **kwargs)


class FabricRoll(models.Model):
    """
    Модель рулона ткани
    """
    fabric_color = models.ForeignKey(FabricColor, on_delete=models.CASCADE, verbose_name="Цвет ткани", related_name="fabric_rolls_from_fabrics")
    width_meters = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        verbose_name="Ширина рулона (м)"  # Используется термин "ширина" по требованию заказчика
    )
    barcode = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="Штрих-код",
        help_text="Уникальный штрих-код рулона"
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name="Активен",
        help_text="Рулон активен (не списан со склада)"
    )
    created_by_admin = models.BooleanField(
        default=False,
        verbose_name="Создан администратором",
        help_text="Рулон создан через интерфейс администратора/бухгалтера"
    )
    notes = models.TextField(
        blank=True, 
        verbose_name="Примечания",
        help_text="Дополнительная информация о клиенте"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = "Рулон ткани"
        verbose_name_plural = "Рулоны тканей"
        ordering = ['-created_at']
    
    def __str__(self):
        status = "активен" if self.is_active else "списан"
        return f"{self.fabric_color} - {self.width_meters}м ({status})"
    
    def save(self, *args, **kwargs):
        if not self.barcode:
            # Генерация уникального штрих-кода
            import random
            import string
            while True:
                barcode = ''.join(random.choices(string.digits, k=6))
                if not FabricRoll.objects.filter(barcode=barcode).exists():
                    self.barcode = barcode
                    break
        super().save(*args, **kwargs)

