from django.db import models
from django.contrib.auth.models import User


class SystemSettings(models.Model):
    """
    Модель системных настроек
    """
    vat_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=20.00,
        verbose_name="НДС (%)",
        help_text="Процент НДС для расчета заказов"
    )
    
    class Meta:
        verbose_name = "Системные настройки"
        verbose_name_plural = "Системные настройки"
    
    def __str__(self):
        return f"НДС: {self.vat_percentage}%"
    
    @classmethod
    def get_current_vat(cls):
        """Получить текущий процент НДС"""
        settings = cls.objects.first()
        return settings.vat_percentage if settings else 20.00


class UserProfile(models.Model):
    """
    Расширение модели пользователя для ролей
    """
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('accountant', 'Бухгалтер'),
        ('warehouse', 'Складовщик')
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        verbose_name="Роль"
    )
    
    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    @property
    def can_view_finances(self):
        """Может ли пользователь видеть финансовую информацию"""
        return self.role in ['admin', 'accountant']
    
    @property
    def can_manage_users(self):
        """Может ли пользователь управлять пользователями"""
        return self.role == 'admin'
    
    @property
    def can_view_financial_analytics(self):
        """Может ли пользователь видеть финансовую аналитику по товарам"""
        return self.role == 'admin'
    
    @property
    def is_warehouse_only(self):
        """Является ли пользователь только складовщиком"""
        return self.role == 'warehouse'


class ActivityLog(models.Model):
    """
    Модель для логирования действий пользователей
    """
    ACTION_CHOICES = [
        ('create', 'Создание'),
        ('update', 'Редактирование'),
        ('delete', 'Удаление'),
        ('barcode_create', 'Создание штрих-кода'),
        ('barcode_scan', 'Сканирование штрих-кода'),
        ('login', 'Вход в систему'),
        ('logout', 'Выход из системы'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="Действие")
    object_type = models.CharField(max_length=50, verbose_name="Тип объекта")
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID объекта")
    description = models.TextField(verbose_name="Описание")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время")
    
    class Meta:
        verbose_name = "Лог активности"
        verbose_name_plural = "Логи активности"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.object_type}"

