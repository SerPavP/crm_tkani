from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta


@login_required
def home(request):
    """Главная страница"""
    # Статистика для главной страницы
    today = timezone.now().date()
    
    # Импортируем модели здесь, чтобы избежать циклических импортов
    from deals.models import Deal
    from fabrics.models import Fabric
    from clients.models import Client
    
    # Для складовщика - перенаправляем на его интерфейс
    if request.user.userprofile.role == 'warehouse':
        return redirect('warehouse:view_rolls')
    
    # Параметры из GET запроса
    period = request.GET.get('period', 'day')  # day, week, month
    deals_type = request.GET.get('deals_type', 'recent')  # recent, pending
    
    # Определяем период для статистики
    if period == 'week':
        # Текущая неделя (понедельник - воскресенье)
        days_since_monday = today.weekday()
        start_date = today - timedelta(days=days_since_monday)
        period_name = "за текущую неделю"
    elif period == 'month':
        # Текущий месяц
        start_date = today.replace(day=1)
        period_name = "за текущий месяц"
    else:  # day
        start_date = today
        period_name = "за сегодня"
    
    # Статистика по выбранному периоду
    period_deals = Deal.objects.filter(created_at__date__gte=start_date)
    period_deals_count = period_deals.count()
    period_revenue = period_deals.filter(status='paid').aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Сделки ожидающие оплаты
    pending_deals = Deal.objects.filter(status='pending_payment')
    pending_deals_count = pending_deals.count()
    
    # Последние 15 сделок
    recent_deals = Deal.objects.all().order_by('-created_at')[:15]
    
    # Выбираем какие сделки показать в основном блоке
    if deals_type == 'pending':
        main_deals = pending_deals[:15]
        main_deals_title = "Сделки ожидающие оплаты"
    else:
        main_deals = recent_deals
        main_deals_title = "Последние сделки"
    
    # Общая статистика
    total_clients = Client.objects.count()
    total_fabrics = Fabric.objects.count()
    total_deals = Deal.objects.count()
    
    context = {
        'period_deals_count': period_deals_count,
        'period_revenue': period_revenue,
        'period_name': period_name,
        'period': period,
        'deals_type': deals_type,
        'pending_deals_count': pending_deals_count,
        'main_deals': main_deals,
        'main_deals_title': main_deals_title,
        'total_clients': total_clients,
        'total_fabrics': total_fabrics,
        'total_deals': total_deals,
    }
    
    return render(request, 'core/home.html', context)


def custom_login(request):
    """Кастомная страница входа"""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        from django.contrib.auth import authenticate
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Создаем UserProfile, если его нет
            from core.models import UserProfile
            if not hasattr(user, 'userprofile'):
                UserProfile.objects.create(user=user, role='admin') # Дефолтная роль
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('core:home')
        else:
            messages.error(request, 'Неверный логин или пароль.')
    
    return render(request, 'core/login.html')


def custom_logout(request):
    """Кастомная функция выхода из системы"""
    # Логируем действие пользователя
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'Вы успешно вышли из системы, {username}!')
    
    return redirect('core:login')

