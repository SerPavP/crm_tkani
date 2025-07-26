from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, Count, Max
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from deals.models import Deal, DealItem
from fabrics.models import Fabric, FabricColor
from .models import SystemSettings
from .forms import SystemSettingsForm
from datetime import date, timedelta, datetime
from decimal import Decimal


@login_required
def financial_dashboard(request):
    """Финансовая аналитика и отчеты"""
    if not hasattr(request.user, 'userprofile') or not request.user.userprofile.can_view_financial_analytics:
        messages.error(request, 'У вас нет прав для просмотра финансовой аналитики.')
        return redirect('core:home')

    # Получаем параметры периода
    date_from = request.GET.get('date_from', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', date.today().strftime('%Y-%m-%d'))
    
    # Конвертируем в объекты date
    if isinstance(date_from, str):
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
    if isinstance(date_to, str):
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    # Текущий период (последние 30 дней)
    current_period_start = date.today() - timedelta(days=30)
    current_period_end = date.today()
    
    # Предыдущий период (30 дней до текущего)
    previous_period_start = current_period_start - timedelta(days=30)
    previous_period_end = current_period_start - timedelta(days=1)
    
    # Функция для расчета прибыли по сделкам
    def calculate_profit_for_deals(deals):
        total_profit = Decimal('0')
        for deal in deals:
            total_profit += deal.total_profit
        return total_profit
    
    # Функция для расчета выручки по сделкам
    def calculate_revenue_for_deals(deals):
        return deals.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0')
    
    # Текущий период
    current_period_deals = Deal.objects.filter(
        created_at__date__gte=current_period_start,
        created_at__date__lte=current_period_end,
        status='paid'
    )
    current_period_revenue = calculate_revenue_for_deals(current_period_deals)
    current_period_profit = calculate_profit_for_deals(current_period_deals)
    current_period_margin = (current_period_profit / current_period_revenue * 100) if current_period_revenue > 0 else 0
    current_period_deals_count = current_period_deals.count()
    current_period_avg_check = current_period_revenue / current_period_deals_count if current_period_deals_count > 0 else 0
    current_period_clients_count = current_period_deals.values('client').distinct().count()
    
    # Предыдущий период
    previous_period_deals = Deal.objects.filter(
        created_at__date__gte=previous_period_start,
        created_at__date__lte=previous_period_end,
        status='paid'
    )
    previous_period_revenue = calculate_revenue_for_deals(previous_period_deals)
    previous_period_profit = calculate_profit_for_deals(previous_period_deals)
    previous_period_margin = (previous_period_profit / previous_period_revenue * 100) if previous_period_revenue > 0 else 0
    previous_period_deals_count = previous_period_deals.count()
    previous_period_avg_check = previous_period_revenue / previous_period_deals_count if previous_period_deals_count > 0 else 0
    previous_period_clients_count = previous_period_deals.values('client').distinct().count()
    
    # Расчет трендов
    revenue_trend = ((current_period_revenue - previous_period_revenue) / previous_period_revenue * 100) if previous_period_revenue > 0 else 0
    profit_trend = ((current_period_profit - previous_period_profit) / previous_period_profit * 100) if previous_period_profit > 0 else 0
    margin_trend = current_period_margin - previous_period_margin
    avg_check_trend = ((current_period_avg_check - previous_period_avg_check) / previous_period_avg_check * 100) if previous_period_avg_check > 0 else 0
    deals_count_trend = current_period_deals_count - previous_period_deals_count
    clients_count_trend = current_period_clients_count - previous_period_clients_count
    
    # Быстрые периоды
    today_deals = Deal.objects.filter(created_at__date=date.today(), status='paid')
    today_revenue = calculate_revenue_for_deals(today_deals)
    today_deals_count = today_deals.count()
    
    week_start = date.today() - timedelta(days=7)
    week_deals = Deal.objects.filter(created_at__date__gte=week_start, created_at__date__lte=date.today(), status='paid')
    week_revenue = calculate_revenue_for_deals(week_deals)
    week_deals_count = week_deals.count()
    
    month_start = date.today() - timedelta(days=30)
    month_deals = Deal.objects.filter(created_at__date__gte=month_start, created_at__date__lte=date.today(), status='paid')
    month_revenue = calculate_revenue_for_deals(month_deals)
    month_deals_count = month_deals.count()
    
    quarter_start = date.today() - timedelta(days=90)
    quarter_deals = Deal.objects.filter(created_at__date__gte=quarter_start, created_at__date__lte=date.today(), status='paid')
    quarter_revenue = calculate_revenue_for_deals(quarter_deals)
    quarter_deals_count = quarter_deals.count()
    
    # Топ-ткань месяца
    top_fabric_month = Fabric.objects.annotate(
        revenue=Sum('fabriccolor__dealitem__total_price')
    ).filter(
        fabriccolor__dealitem__deal__created_at__date__gte=month_start,
        fabriccolor__dealitem__deal__created_at__date__lte=date.today(),
        fabriccolor__dealitem__deal__status='paid'
    ).order_by('-revenue').first()
    
    if not top_fabric_month or not top_fabric_month.revenue:
        top_fabric_month = type('obj', (object,), {'name': 'Нет данных', 'revenue': 0})()
    
    # Оборачиваемость (среднее время между заказами)
    all_deals = Deal.objects.filter(status='paid').order_by('created_at')
    if all_deals.count() > 1:
        first_deal = all_deals.first()
        last_deal = all_deals.last()
        total_days = (last_deal.created_at.date() - first_deal.created_at.date()).days
        turnover_days = total_days / all_deals.count() if all_deals.count() > 0 else 0
    else:
        turnover_days = 0
    
    # Топ-5 клиентов по прибыли
    top_clients_by_profit = []
    clients_profit = Deal.objects.filter(status='paid').values('client__nickname', 'client__id').annotate(
        total_amount=Sum('total_amount')
    ).order_by('-total_amount')[:5]
    
    total_profit_all = calculate_profit_for_deals(Deal.objects.filter(status='paid'))
    
    for client_data in clients_profit:
        client_id = client_data.get('client__id')
        if client_id is None:
            # Пропускаем, если client_id равен None
            continue
        
        # Получаем все сделки клиента для расчета прибыли
        client_deals = Deal.objects.filter(
            status='paid',
            client__id=client_id
        )
        client_total_profit = calculate_profit_for_deals(client_deals)
        profit_percentage = (client_total_profit / total_profit_all * 100) if total_profit_all > 0 else 0
        top_clients_by_profit.append({
            'nickname': client_data['client__nickname'],
            'id': client_id,
            'total_profit': client_total_profit,
            'profit_percentage': profit_percentage
        })
    
    # Сортируем по прибыли
    top_clients_by_profit.sort(key=lambda x: x['total_profit'], reverse=True)
    top_clients_by_profit = top_clients_by_profit[:5]
    
    # Топ-5 клиентов по количеству сделок
    top_clients_by_count = []
    clients_count = Deal.objects.filter(status='paid').values('client__nickname', 'client__id').annotate(
        deals_count=Count('id'),
        total_sum=Sum('total_amount')
    ).order_by('-deals_count')[:5]
    
    for client_data in clients_count:
        client_id = client_data.get('client__id')
        if client_id is None:
            # Пропускаем, если client_id равен None
            continue
            
        avg_check = client_data['total_sum'] / client_data['deals_count'] if client_data['deals_count'] > 0 else 0
        top_clients_by_count.append({
            'nickname': client_data['client__nickname'],
            'id': client_id,
            'deals_count': client_data['deals_count'],
            'avg_check': avg_check
        })
    
    # Топ-5 клиентов по общей сумме
    top_clients_by_sum = []
    clients_sum = Deal.objects.filter(status='paid').values('client__nickname', 'client__id').annotate(
        total_sum=Sum('total_amount'),
        last_purchase=Max('created_at')
    ).order_by('-total_sum')[:5]
    
    for client_data in clients_sum:
        client_id = client_data.get('client__id')
        if client_id is None:
            # Пропускаем, если client_id равен None
            continue
            
        top_clients_by_sum.append({
            'nickname': client_data['client__nickname'],
            'id': client_id,
            'total_sum': client_data['total_sum'],
            'last_purchase': client_data['last_purchase']
        })
    
    # Топ-5 тканей по метрам
    top_fabrics_by_meters = []
    fabrics_meters = DealItem.objects.filter(deal__status='paid').values(
        'fabric_color__fabric__name', 'fabric_color__color_name', 'fabric_color__fabric__id'
    ).annotate(
        total_meters=Sum('width_meters'),
        order_frequency=Count('deal', distinct=True)
    ).order_by('-order_frequency')[:5]
    
    for fabric_data in fabrics_meters:
        fabric_main_id = fabric_data.get('fabric_color__fabric__id')
        if fabric_main_id is None:
            continue
        top_fabrics_by_meters.append({
            'name': fabric_data['fabric_color__fabric__name'],
            'color': fabric_data['fabric_color__color_name'],
            'id': fabric_main_id,
            'total_meters': fabric_data['total_meters'],
            'order_frequency': fabric_data['order_frequency']
        })
    
    # Топ-5 тканей по прибыли
    top_fabrics_by_profit = []
    fabrics_profit = DealItem.objects.filter(deal__status='paid').values(
        'fabric_color__fabric__name', 'fabric_color__color_name', 'fabric_color__fabric__id'
    ).annotate(
        total_revenue=Sum('total_price'),
        total_cost=Sum(F('width_meters') * F('fabric_color__fabric__cost_price'))
    ).order_by('-total_revenue')[:5]
    
    for fabric_data in fabrics_profit:
        fabric_main_id = fabric_data.get('fabric_color__fabric__id')
        if fabric_main_id is None:
            continue
        total_profit = fabric_data['total_revenue'] - fabric_data['total_cost']
        margin = (total_profit / fabric_data['total_revenue'] * 100) if fabric_data['total_revenue'] > 0 else 0
        top_fabrics_by_profit.append({
            'name': fabric_data['fabric_color__fabric__name'],
            'color': fabric_data['fabric_color__color_name'],
            'id': fabric_main_id,
            'total_profit': total_profit,
            'margin': margin
        })
    
    # Топ-5 тканей по выручке
    top_fabrics_by_revenue = []
    total_revenue_all = DealItem.objects.filter(deal__status='paid').aggregate(
        total=Sum('total_price')
    )['total'] or Decimal('0')
    
    fabrics_revenue = DealItem.objects.filter(deal__status='paid').values(
        'fabric_color__fabric__name', 'fabric_color__color_name', 'fabric_color__fabric__id'
    ).annotate(
        total_revenue=Sum('total_price')
    ).order_by('-total_revenue')[:5]
    
    for fabric_data in fabrics_revenue:
        fabric_main_id = fabric_data.get('fabric_color__fabric__id')
        if fabric_main_id is None:
            continue
        revenue_percentage = (fabric_data['total_revenue'] / total_revenue_all * 100) if total_revenue_all > 0 else 0
        top_fabrics_by_revenue.append({
            'name': fabric_data['fabric_color__fabric__name'],
            'color': fabric_data['fabric_color__color_name'],
            'id': fabric_main_id,
            'total_revenue': fabric_data['total_revenue'],
            'revenue_percentage': revenue_percentage
        })
    
    # Данные для периода (если указаны даты)
    period_deals = Deal.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status='paid'
    )
    period_revenue = calculate_revenue_for_deals(period_deals)
    period_profit = calculate_profit_for_deals(period_deals)
    period_margin = (period_profit / period_revenue * 100) if period_revenue > 0 else 0
    period_deals_count = period_deals.count()
    period_avg_check = period_revenue / period_deals_count if period_deals_count > 0 else 0

    context = {
        # KPI-блоки
        'current_period_revenue': current_period_revenue,
        'current_period_profit': current_period_profit,
        'current_period_margin': current_period_margin,
        'current_period_deals_count': current_period_deals_count,
        'current_period_avg_check': current_period_avg_check,
        
        # Тренды
        'revenue_trend': revenue_trend,
        'profit_trend': profit_trend,
        'margin_trend': margin_trend,
        'avg_check_trend': avg_check_trend,
        'deals_count_trend': deals_count_trend,
        
        # Быстрые периоды
        'today_revenue': today_revenue,
        'today_deals_count': today_deals_count,
        'week_revenue': week_revenue,
        'week_deals_count': week_deals_count,
        'month_revenue': month_revenue,
        'month_deals_count': month_deals_count,
        'quarter_revenue': quarter_revenue,
        'quarter_deals_count': quarter_deals_count,
        
        'today_iso': date.today().strftime('%Y-%m-%d'),
        'week_start_iso': (date.today() - timedelta(days=7)).strftime('%Y-%m-%d'),
        'month_start_iso': (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'),
        'quarter_start_iso': (date.today() - timedelta(days=90)).strftime('%Y-%m-%d'),
        'year_start_iso': (date.today() - timedelta(days=365)).strftime('%Y-%m-%d'),

        # Топ-ткань месяца
        'top_fabric_month': top_fabric_month,
        
        # Оборачиваемость
        'turnover_days': turnover_days,
        'turnover_trend': 0,  # Можно добавить расчет тренда
        
        # Топ-клиенты
        'top_clients_by_profit': top_clients_by_profit,
        'top_clients_by_count': top_clients_by_count,
        'top_clients_by_sum': top_clients_by_sum,
        
        # Топ-ткани
        'top_fabrics_by_meters': top_fabrics_by_meters,
        'top_fabrics_by_profit': top_fabrics_by_profit,
        'top_fabrics_by_revenue': top_fabrics_by_revenue,
        
        # Данные для периода
        'date_from': date_from,
        'date_to': date_to,
        'period_revenue': period_revenue,
        'period_profit': period_profit,
        'period_margin': period_margin,
        'period_deals_count': period_deals_count,
        'period_avg_check': period_avg_check,
        'period_deals': period_deals,
    }
    
    return render(request, 'finances/financial_dashboard.html', context)


@login_required
def system_settings(request):
    """Настройки системы (НДС)"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        messages.error(request, 'У вас нет прав для доступа к настройкам системы.')
        return redirect('core:home')

    settings_obj = SystemSettings.load()

    if request.method == 'POST':
        form = SystemSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Настройки успешно обновлены.')
            return redirect('finances:system_settings')
    else:
        form = SystemSettingsForm(instance=settings_obj)

    # (pr2) Добавить view для экспорта данных
    # (pr2) Добавить view для импорта данных
    # (pr2) Добавить view для очистки данных
    # (pr2) Добавить view для резервной копии

    # Импортируем модели для статистики
    from django.contrib.auth.models import User
    from clients.models import Client
    from deals.models import Deal
    from fabrics.models import Fabric, FabricRoll
    
    # Получаем всех пользователей кроме текущего
    all_users = User.objects.exclude(id=request.user.id)
    
    # Собираем статистику
    total_clients = Client.objects.count()
    total_deals = Deal.objects.count()
    total_fabrics = Fabric.objects.count()
    active_rolls = FabricRoll.objects.filter(is_active=True).count()

    context = {
        'form': form,
        'all_users': all_users,
        'total_clients': total_clients,
        'total_deals': total_deals,
        'total_fabrics': total_fabrics,
        'active_rolls': active_rolls,
    }
    return render(request, 'finances/system_settings.html', context)


@login_required
def update_user_name(request):
    """Обновление имени пользователя (только для админа)"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return JsonResponse({'success': False, 'error': 'Нет прав для выполнения операции'})
    
    if request.method == 'POST':
        try:
            from django.contrib.auth.models import User
            
            user_id = request.POST.get('user_id')
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            
            if not user_id:
                return JsonResponse({'success': False, 'error': 'ID пользователя не указан'})
            
            user_to_update = User.objects.get(id=user_id)
            
            # Запрещаем изменять данные самого админа
            if user_to_update.id == request.user.id:
                return JsonResponse({'success': False, 'error': 'Нельзя изменять свои данные'})
            
            user_to_update.first_name = first_name
            user_to_update.last_name = last_name
            user_to_update.save()
            
            return JsonResponse({'success': True})
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Пользователь не найден'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})


@login_required
def recreate_user(request):
    """Переделка пользователя заново (только для админа)"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return JsonResponse({'success': False, 'error': 'Нет прав для выполнения операции'})
    
    if request.method == 'POST':
        try:
            from django.contrib.auth.models import User
            
            user_id = request.POST.get('user_id')
            new_password = request.POST.get('new_password')
            
            if not user_id or not new_password:
                return JsonResponse({'success': False, 'error': 'Не указаны обязательные параметры'})
            
            user_to_recreate = User.objects.get(id=user_id)
            
            # Запрещаем переделывать самого админа
            if user_to_recreate.id == request.user.id:
                return JsonResponse({'success': False, 'error': 'Нельзя переделывать свой аккаунт'})
            
            # Обновляем пользователя
            user_to_recreate.set_password(new_password)
            user_to_recreate.first_name = ''
            user_to_recreate.last_name = ''
            user_to_recreate.save()
            
            return JsonResponse({'success': True})
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Пользователь не найден'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})


@login_required
def change_user_password(request):
    """Смена пароля пользователя (только для админа)"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return JsonResponse({'success': False, 'error': 'Нет прав для выполнения операции'})
    
    if request.method == 'POST':
        try:
            from django.contrib.auth.models import User
            
            user_id = request.POST.get('user_id')
            new_password = request.POST.get('new_password')
            
            if not user_id or not new_password:
                return JsonResponse({'success': False, 'error': 'Не указаны обязательные параметры'})
            
            user_to_update = User.objects.get(id=user_id)
            
            # Запрещаем изменять пароль самого админа
            if user_to_update.id == request.user.id:
                return JsonResponse({'success': False, 'error': 'Нельзя изменять свой пароль через эту функцию'})
            
            user_to_update.set_password(new_password)
            user_to_update.save()
            
            return JsonResponse({'success': True})
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Пользователь не найден'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})


@login_required
def update_fabric_prices(request):
    """Обновление цен ткани (только для админа)"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return JsonResponse({'success': False, 'error': 'Нет прав для выполнения операции'})
    
    if request.method == 'POST':
        try:
            from fabrics.models import Fabric
            
            fabric_id = request.POST.get('fabric_id')
            cost_price = request.POST.get('cost_price')
            selling_price = request.POST.get('selling_price')
            
            if not fabric_id or not cost_price or not selling_price:
                return JsonResponse({'success': False, 'error': 'Не указаны обязательные параметры'})
            
            fabric = Fabric.objects.get(id=fabric_id)
            fabric.cost_price = float(cost_price)
            fabric.selling_price = float(selling_price)
            fabric.save()
            
            return JsonResponse({
                'success': True,
                'cost_price': str(fabric.cost_price),
                'selling_price': str(fabric.selling_price)
            })
            
        except Fabric.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Ткань не найдена'})
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Некорректные значения цен'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})


@login_required
def get_markup_percentage(request):
    """API для получения процента наценки"""
    try:
        settings = SystemSettings.load()
        return JsonResponse({'markup_percentage': float(settings.markup_percentage)})
    except:
        return JsonResponse({'markup_percentage': 20.00})


@login_required
def set_fabric_cost_price(request):
    """Установка себестоимости ткани (для всех цветов)"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        messages.error(request, 'У вас нет прав для установки себестоимости ткани.')
        return redirect('core:home')

    if request.method == 'POST':
        fabric_id = request.POST.get('fabric_id')
        cost_price = request.POST.get('cost_price')

        try:
            fabric = Fabric.objects.get(id=fabric_id)
            if fabric:
                fabric.cost_price = cost_price
                fabric.save()
                messages.success(request, f'Себестоимость для ткани {fabric.name} успешно обновлена.')
            else:
                messages.error(request, 'Ткань не найдена.')
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении себестоимости: {e}')

        return redirect('finances:set_fabric_cost_price') # Redirect back to this page

    # For GET request, render a form or a list of fabrics to set cost price
    fabrics = Fabric.objects.all().order_by('name')
    context = {
        'fabrics': fabrics
    }
    return render(request, 'finances/set_fabric_cost_price.html', context)


@login_required
@require_POST
def change_password(request):
    """Смена пароля пользователя (только для админа)"""
    if request.user.userprofile.role != 'admin':
        return JsonResponse({'error': 'Нет прав доступа'}, status=403)
    
    user_id = request.POST.get('user_id')
    new_password = request.POST.get('new_password')
    
    if not user_id or not new_password:
        return JsonResponse({'error': 'Необходимо указать ID пользователя и новый пароль'}, status=400)
    
    if len(new_password) < 6:
        return JsonResponse({'error': 'Пароль должен содержать минимум 6 символов'}, status=400)
    
    try:
        user = User.objects.get(id=user_id)
        user.set_password(new_password)
        user.save()
        
        return JsonResponse({'success': True, 'message': f'Пароль для пользователя {user.username} успешно изменен'})
    
    except User.DoesNotExist:
        return JsonResponse({'error': 'Пользователь не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Ошибка при смене пароля: {str(e)}'}, status=500)



from fabrics.models import Fabric


@login_required
def get_period_data(request):
    """Возвращает данные по сделкам за указанный период в JSON формате"""
    if not hasattr(request.user, 'userprofile') or not request.user.userprofile.can_view_financial_analytics:
        return JsonResponse({'error': 'У вас нет прав для просмотра финансовой аналитики.'}, status=403)

    from datetime import datetime, date, timedelta
    from decimal import Decimal
    from django.db.models import Sum, F
    from deals.templatetags.deal_filters import format_price

    date_from_str = request.GET.get('date_from')
    date_to_str = request.GET.get('date_to')

    today = date.today()

    if date_from_str and date_to_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Неверный формат даты.'}, status=400)
    else:
        # Значения по умолчанию, если даты не указаны
        date_from = today - timedelta(days=30)
        date_to = today

    period_deals = Deal.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status='paid'
    ).order_by('-created_at')

    def calculate_profit_for_deals(deals):
        total_profit = Decimal('0')
        for deal in deals:
            total_profit += deal.total_profit
        return total_profit

    period_revenue = period_deals.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0')
    period_profit = calculate_profit_for_deals(period_deals)
    period_margin = (period_profit / period_revenue * 100) if period_revenue > 0 else 0
    period_deals_count = period_deals.count()
    period_avg_check = period_revenue / period_deals_count if period_deals_count > 0 else Decimal('0')

    deals_data = []
    for deal in period_deals:
        deals_data.append({
            'id': deal.id,
            'created_at': deal.created_at.strftime('%d.%m.%Y'),
            'deal_number': deal.deal_number[:11] + ('...' if len(deal.deal_number) > 11 else ''),
            'client_nickname': deal.client.nickname,
            'status_display': deal.get_status_display(),
            'status_class': 'bg-warning' if deal.status == 'pending_payment' else ('bg-success' if deal.status == 'paid' else 'bg-secondary'),
            'total_amount': format_price(deal.total_amount),
            'total_profit': format_price(deal.total_profit),
            'margin': f"{deal.total_profit / deal.total_amount * 100:.1f}" if deal.total_amount > 0 else '0',
            'items_count': deal.dealitem_set.count()
        })

    response_data = {
        'date_from': date_from.strftime('%d.%m.%Y'),
        'date_to': date_to.strftime('%d.%m.%Y'),
        'period_revenue': format_price(period_revenue),
        'period_profit': format_price(period_profit),
        'period_margin': f"{period_margin:.1f}",
        'period_deals_count': period_deals_count,
        'period_avg_check': format_price(period_avg_check),
        'deals': deals_data
    }

    return JsonResponse(response_data)

