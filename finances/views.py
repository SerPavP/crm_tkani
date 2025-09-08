from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, Count, Max, Q, Case, When
from django.db import models
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from deals.models import Deal, DealItem
from fabrics.models import Fabric, FabricColor, FabricRoll
from clients.models import Client
from .models import SystemSettings
from .forms import SystemSettingsForm
from datetime import timedelta, datetime
from django.utils import timezone
from django.core.cache import cache
from decimal import Decimal
import calendar
import hashlib


@login_required
def financial_dashboard(request):
    """Финансовая аналитика и отчеты (оптимизированная версия)"""
    if not hasattr(request.user, 'userprofile') or not request.user.userprofile.can_view_financial_analytics:
        messages.error(request, 'У вас нет прав для просмотра финансовой аналитики.')
        return redirect('core:home')

    # Кеширование дорогих вычислений на 5 минут
    cache_key = f"financial_dashboard_data:{request.user.id}:{hashlib.md5(request.META.get('QUERY_STRING', '').encode()).hexdigest()}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render(request, 'finances/financial_dashboard.html', cached_data)

    today = timezone.localdate()
    
    # Получаем параметры периода
    date_from = request.GET.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', today.strftime('%Y-%m-%d'))
    
    # Конвертируем в объекты date
    if isinstance(date_from, str):
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
    if isinstance(date_to, str):
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    # Определяем периоды
    # Текущий календарный месяц (с 1 числа до сегодня)
    current_period_start = today.replace(day=1)
    current_period_end = today
    
    # Предыдущий календарный месяц
    if today.month == 1:
        prev_month = today.replace(year=today.year-1, month=12, day=1)
    else:
        prev_month = today.replace(month=today.month-1, day=1)
    
    # Последний день предыдущего месяца
    import calendar
    last_day = calendar.monthrange(prev_month.year, prev_month.month)[1]
    previous_period_start = prev_month
    previous_period_end = prev_month.replace(day=last_day)
    
    week_start = today - timedelta(days=6)
    month_start = today - timedelta(days=32)  # Изменено с 29 на 32 дня
    quarter_start = today - timedelta(days=89)
    year_start = today - timedelta(days=364)

    # ОПТИМИЗИРОВАННЫЙ ЗАПРОС: Получаем все необходимые данные одним запросом
    all_deals = Deal.objects.filter(status='paid').prefetch_related('dealitem_set__fabric_color__fabric')
    
    # Агрегированные данные по периодам одним запросом
    period_stats = all_deals.aggregate(
        # Текущий период
        current_revenue=Sum(
            Case(
                When(Q(created_at__date__gte=current_period_start) & Q(created_at__date__lte=current_period_end), 
                     then='total_amount'),
                default=0,
                output_field=models.DecimalField()
            )
        ),
        current_count=Count(
            Case(
                When(Q(created_at__date__gte=current_period_start) & Q(created_at__date__lte=current_period_end), 
                     then='id'),
                output_field=models.IntegerField()
            )
        ),
        # Предыдущий период
        previous_revenue=Sum(
            Case(
                When(Q(created_at__date__gte=previous_period_start) & Q(created_at__date__lte=previous_period_end), 
                     then='total_amount'),
                default=0,
                output_field=models.DecimalField()
            )
        ),
        previous_count=Count(
            Case(
                When(Q(created_at__date__gte=previous_period_start) & Q(created_at__date__lte=previous_period_end), 
                     then='id'),
                output_field=models.IntegerField()
            )
        ),
        # Быстрые периоды
        today_revenue=Sum(
            Case(
                When(created_at__date=today, then='total_amount'),
                default=0,
                output_field=models.DecimalField()
            )
        ),
        today_count=Count(
            Case(
                When(created_at__date=today, then='id'),
                output_field=models.IntegerField()
            )
        ),
        week_revenue=Sum(
            Case(
                When(Q(created_at__date__gte=week_start) & Q(created_at__date__lte=today), 
                     then='total_amount'),
                default=0,
                output_field=models.DecimalField()
            )
        ),
        week_count=Count(
            Case(
                When(Q(created_at__date__gte=week_start) & Q(created_at__date__lte=today), 
                     then='id'),
                output_field=models.IntegerField()
            )
        ),
        month_revenue=Sum(
            Case(
                When(Q(created_at__date__gte=month_start) & Q(created_at__date__lte=today), 
                     then='total_amount'),
                default=0,
                output_field=models.DecimalField()
            )
        ),
        month_count=Count(
            Case(
                When(Q(created_at__date__gte=month_start) & Q(created_at__date__lte=today), 
                     then='id'),
                output_field=models.IntegerField()
            )
        ),
        quarter_revenue=Sum(
            Case(
                When(Q(created_at__date__gte=quarter_start) & Q(created_at__date__lte=today), 
                     then='total_amount'),
                default=0,
                output_field=models.DecimalField()
            )
        ),
        quarter_count=Count(
            Case(
                When(Q(created_at__date__gte=quarter_start) & Q(created_at__date__lte=today), 
                     then='id'),
                output_field=models.IntegerField()
            )
        ),
        year_revenue=Sum(
            Case(
                When(Q(created_at__date__gte=year_start) & Q(created_at__date__lte=today), 
                     then='total_amount'),
                default=0,
                output_field=models.DecimalField()
            )
        ),
        year_count=Count(
            Case(
                When(Q(created_at__date__gte=year_start) & Q(created_at__date__lte=today), 
                     then='id'),
                output_field=models.IntegerField()
            )
        )
    )
    
    # Извлекаем значения с нулевыми значениями по умолчанию
    current_period_revenue = period_stats['current_revenue'] or Decimal('0')
    current_period_deals_count = period_stats['current_count'] or 0
    previous_period_revenue = period_stats['previous_revenue'] or Decimal('0')
    previous_period_deals_count = period_stats['previous_count'] or 0
    
    today_revenue = period_stats['today_revenue'] or Decimal('0')
    today_deals_count = period_stats['today_count'] or 0
    week_revenue = period_stats['week_revenue'] or Decimal('0')
    week_deals_count = period_stats['week_count'] or 0
    month_revenue = period_stats['month_revenue'] or Decimal('0')
    month_deals_count = period_stats['month_count'] or 0
    quarter_revenue = period_stats['quarter_revenue'] or Decimal('0')
    quarter_deals_count = period_stats['quarter_count'] or 0
    year_revenue = period_stats['year_revenue'] or Decimal('0')
    year_deals_count = period_stats['year_count'] or 0

    # Быстрое вычисление прибыли (оптимизированное)
    def calculate_profit_optimized(deal_filter_q):
        return DealItem.objects.filter(
            deal__status='paid'
        ).filter(deal_filter_q).aggregate(
            profit=Sum(
                F('total_price') - F('width_meters') * Case(
                    When(fixed_cost_price__isnull=False, then=F('fixed_cost_price')),
                    default=F('fabric_color__fabric__cost_price'),
                    output_field=models.DecimalField()
                ),
                output_field=models.DecimalField()
            )
        )['profit'] or Decimal('0')
    
    current_period_profit = calculate_profit_optimized(
        Q(deal__created_at__date__gte=current_period_start) & 
        Q(deal__created_at__date__lte=current_period_end)
    )
    previous_period_profit = calculate_profit_optimized(
        Q(deal__created_at__date__gte=previous_period_start) & 
        Q(deal__created_at__date__lte=previous_period_end)
    )
    
    # Расчеты метрик
    current_period_margin = (current_period_profit / current_period_revenue * 100) if current_period_revenue > 0 else 0
    current_period_avg_check = current_period_revenue / current_period_deals_count if current_period_deals_count > 0 else 0
    previous_period_margin = (previous_period_profit / previous_period_revenue * 100) if previous_period_revenue > 0 else 0
    previous_period_avg_check = previous_period_revenue / previous_period_deals_count if previous_period_deals_count > 0 else 0
    
    # Тренды
    revenue_trend = ((current_period_revenue - previous_period_revenue) / previous_period_revenue * 100) if previous_period_revenue > 0 else 0
    profit_trend = ((current_period_profit - previous_period_profit) / previous_period_profit * 100) if previous_period_profit > 0 else 0
    margin_trend = current_period_margin - previous_period_margin
    avg_check_trend = ((current_period_avg_check - previous_period_avg_check) / previous_period_avg_check * 100) if previous_period_avg_check > 0 else 0
    deals_count_trend = current_period_deals_count - previous_period_deals_count
    
    # Рулоны (быстрый запрос)
    rolls_stats = FabricRoll.objects.aggregate(
        current_rolls=Count(
            Case(
                When(Q(created_at__date__gte=current_period_start) & Q(created_at__date__lte=current_period_end), 
                     then='id'),
                output_field=models.IntegerField()
            )
        ),
        previous_rolls=Count(
            Case(
                When(Q(created_at__date__gte=previous_period_start) & Q(created_at__date__lte=previous_period_end), 
                     then='id'),
                output_field=models.IntegerField()
            )
        )
    )
    
    current_period_rolls_count = rolls_stats['current_rolls'] or 0
    previous_period_rolls_count = rolls_stats['previous_rolls'] or 0
    rolls_count_trend = current_period_rolls_count - previous_period_rolls_count
    
    # Топ-ткань месяца (быстрый запрос)
    top_fabric_month = Fabric.objects.annotate(
        revenue=Sum('fabriccolor__dealitem__total_price')
    ).filter(
        fabriccolor__dealitem__deal__created_at__date__gte=month_start,
        fabriccolor__dealitem__deal__created_at__date__lte=today,
        fabriccolor__dealitem__deal__status='paid'
    ).order_by('-revenue').first()
    
    if not top_fabric_month or not top_fabric_month.revenue:
        top_fabric_month = type('obj', (object,), {'name': 'Нет данных', 'revenue': 0})()
    
    # Оборачиваемость (упрощенный расчет)
    all_deals_count = all_deals.count()
    if all_deals_count > 1:
        first_deal = all_deals.order_by('created_at').first()
        last_deal = all_deals.order_by('-created_at').first()
        if first_deal and last_deal:
            total_days = (last_deal.created_at.date() - first_deal.created_at.date()).days
            turnover_days = total_days / (all_deals_count - 1) if all_deals_count > 1 else 0
        else:
            turnover_days = 0
    else:
        turnover_days = 0

    # ОПТИМИЗИРОВАННЫЕ ТОП-СПИСКИ (объединенные запросы)
    
    # Топ-5 клиентов (все в одном запросе)
    top_clients_data = Deal.objects.filter(status='paid').values(
        'client__id', 'client__nickname'
    ).annotate(
        total_revenue=Sum('total_amount'),
        deals_count=Count('id'),
        last_purchase=Max('created_at')
    ).order_by('-total_revenue')[:5]
    
    top_clients_by_profit = []
    top_clients_by_count = []
    top_clients_by_sum = []
    
    for client_data in top_clients_data:
        if client_data['client__id'] is None:
            continue
            
        # Для топ по сумме
        top_clients_by_sum.append({
            'nickname': client_data['client__nickname'],
            'id': client_data['client__id'],
            'total_sum': client_data['total_revenue'],
            'last_purchase': client_data['last_purchase']
        })
        
        # Для топ по количеству
        avg_check = client_data['total_revenue'] / client_data['deals_count'] if client_data['deals_count'] > 0 else 0
        top_clients_by_count.append({
            'nickname': client_data['client__nickname'],
            'id': client_data['client__id'],
            'deals_count': client_data['deals_count'],
            'avg_check': avg_check
        })
    
    # Пересортируем по количеству сделок
    top_clients_by_count.sort(key=lambda x: x['deals_count'], reverse=True)
    top_clients_by_count = top_clients_by_count[:5]
    
    # Топ клиентов по прибыли (отдельный оптимизированный запрос)
    clients_profit_data = DealItem.objects.filter(
        deal__status='paid'
    ).values(
        'deal__client__id', 'deal__client__nickname'
    ).annotate(
        total_profit=Sum(
            F('total_price') - F('width_meters') * Case(
                When(fixed_cost_price__isnull=False, then=F('fixed_cost_price')),
                default=F('fabric_color__fabric__cost_price'),
                output_field=models.DecimalField()
            ),
            output_field=models.DecimalField()
        )
    ).order_by('-total_profit')[:5]
    
    total_profit_all = DealItem.objects.filter(deal__status='paid').aggregate(
        total=Sum(
            F('total_price') - F('width_meters') * Case(
                When(fixed_cost_price__isnull=False, then=F('fixed_cost_price')),
                default=F('fabric_color__fabric__cost_price'),
                output_field=models.DecimalField()
            ),
            output_field=models.DecimalField()
        )
    )['total'] or Decimal('0')
    
    for client_data in clients_profit_data:
        if client_data['deal__client__id'] is None:
            continue
            
        client_total_profit = client_data['total_profit'] or Decimal('0')
        profit_percentage = (client_total_profit / total_profit_all * 100) if total_profit_all > 0 else 0
        
        top_clients_by_profit.append({
            'nickname': client_data['deal__client__nickname'],
            'id': client_data['deal__client__id'],
            'total_profit': client_total_profit,
            'profit_percentage': profit_percentage
        })

    # Топ-5 тканей (объединенный оптимизированный запрос)
    top_fabrics_data = DealItem.objects.filter(deal__status='paid').values(
        'fabric_color__fabric__name', 'fabric_color__color_name', 'fabric_color__fabric__id'
    ).annotate(
        total_meters=Sum('width_meters'),
        order_frequency=Count('deal', distinct=True),
        total_revenue=Sum('total_price'),
        total_cost=Sum(F('width_meters') * Case(
            When(fixed_cost_price__isnull=False, then=F('fixed_cost_price')),
            default=F('fabric_color__fabric__cost_price'),
            output_field=models.DecimalField()
        ))
    ).order_by('-order_frequency')[:5]
    
    top_fabrics_by_meters = []
    top_fabrics_by_profit = []
    top_fabrics_by_revenue = []
    
    total_revenue_all = DealItem.objects.filter(deal__status='paid').aggregate(
        total=Sum('total_price')
    )['total'] or Decimal('0')
    
    for fabric_data in top_fabrics_data:
        if fabric_data['fabric_color__fabric__id'] is None:
            continue
        
        # Для топ по метрам
        top_fabrics_by_meters.append({
            'name': fabric_data['fabric_color__fabric__name'],
            'color': fabric_data['fabric_color__color_name'],
            'id': fabric_data['fabric_color__fabric__id'],
            'total_meters': fabric_data['total_meters'],
            'order_frequency': fabric_data['order_frequency']
        })
        
        # Для топ по прибыли
        total_profit = fabric_data['total_revenue'] - fabric_data['total_cost']
        margin = (total_profit / fabric_data['total_revenue'] * 100) if fabric_data['total_revenue'] > 0 else 0
        top_fabrics_by_profit.append({
            'name': fabric_data['fabric_color__fabric__name'],
            'color': fabric_data['fabric_color__color_name'],
            'id': fabric_data['fabric_color__fabric__id'],
            'total_profit': total_profit,
            'margin': margin
        })
        
        # Для топ по выручке
        revenue_percentage = (fabric_data['total_revenue'] / total_revenue_all * 100) if total_revenue_all > 0 else 0
        top_fabrics_by_revenue.append({
            'name': fabric_data['fabric_color__fabric__name'],
            'color': fabric_data['fabric_color__color_name'],
            'id': fabric_data['fabric_color__fabric__id'],
            'total_revenue': fabric_data['total_revenue'],
            'revenue_percentage': revenue_percentage
        })
    
    # Пересортируем списки
    top_fabrics_by_profit.sort(key=lambda x: x['total_profit'], reverse=True)
    top_fabrics_by_revenue.sort(key=lambda x: x['total_revenue'], reverse=True)
    
    # Данные для графика (только заработок, остальные убраны)
    month_start_chart = today.replace(day=1)
    weekly_revenue = []
    week_labels = []
    
    current_period_start_chart = month_start_chart
    while current_period_start_chart <= today:
        period_end = min(current_period_start_chart + timedelta(days=2), today)
        
        period_revenue_value = Deal.objects.filter(
            created_at__date__gte=current_period_start_chart,
            created_at__date__lte=period_end,
            status='paid'
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0')
        
        weekly_revenue.append(float(period_revenue_value))
        week_labels.append(f"{current_period_start_chart.strftime('%d.%m')}-{period_end.strftime('%d.%m')}")
        
        current_period_start_chart = period_end + timedelta(days=1)

    # Упрощенные топ-20 (только для админов)
    top_20_clients_by_revenue = []
    top_20_clients_by_count = []
    top_20_clients_by_profit = []
    top_20_fabrics_by_orders = []
    top_20_fabrics_by_meters = []
    top_20_fabrics_by_profit = []

    # Параметры периода для Топ-20 (месяц/год, с возможностью диапазона)
    top20_mode = request.GET.get('top20_mode', 'month')  # 'month' или 'year'
    # Значения по умолчанию — текущий месяц / текущий год
    default_month = today.strftime('%Y-%m')
    default_year = today.strftime('%Y')

    top20_month_from = request.GET.get('top20_month_from', default_month)
    top20_month_to = request.GET.get('top20_month_to', default_month)
    top20_year_from = request.GET.get('top20_year_from', default_year)
    top20_year_to = request.GET.get('top20_year_to', default_year)

    # Вычисляем границы дат для выбранного режима
    if top20_mode == 'year':
        try:
            y_from = int(top20_year_from)
            y_to = int(top20_year_to)
            if y_from > y_to:
                y_from, y_to = y_to, y_from
        except Exception:
            y_from = int(default_year)
            y_to = int(default_year)
        top20_start_date = datetime(y_from, 1, 1).date()
        top20_end_date = datetime(y_to, 12, 31).date()
    else:
        # Режим месяцев
        try:
            y1, m1 = map(int, top20_month_from.split('-'))
            y2, m2 = map(int, top20_month_to.split('-'))
            # Нормализуем порядок
            d1 = datetime(y1, m1, 1).date()
            last_day_m2 = calendar.monthrange(y2, m2)[1]
            d2 = datetime(y2, m2, last_day_m2).date()
            if d1 > d2:
                d1, d2 = d2, d1
            top20_start_date, top20_end_date = d1, d2
        except Exception:
            y, m = map(int, default_month.split('-'))
            top20_start_date = datetime(y, m, 1).date()
            top20_end_date = datetime(y, m, calendar.monthrange(y, m)[1]).date()

    top20_date_filter_q = Q(deal__created_at__date__gte=top20_start_date) & Q(deal__created_at__date__lte=top20_end_date)

    if hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin':
        # Быстрые запросы для топ-20 (клиенты)
        raw_top20 = list(
            Deal.objects.filter(status='paid', created_at__date__gte=top20_start_date, created_at__date__lte=top20_end_date)
            .values('client__id', 'client__nickname', 'client__phone')
            .annotate(
                total_revenue=Sum('total_amount'),
                deals_count=Count('id')
            )
            .order_by('-total_revenue')[:20]
        )
        
        # Собираем объекты клиентов одним запросом
        client_ids = [row['client__id'] for row in raw_top20 if row['client__id']]
        clients_by_id = {c.id: c for c in Client.objects.filter(id__in=client_ids)}
        
        # Формируем структуру (client объект, total_revenue, total_deals)
        top_20_clients_by_revenue = [
            {
                'client': clients_by_id.get(row['client__id']) or type('obj', (object,), {
                    'id': row['client__id'],
                    'nickname': row['client__nickname'],
                    'phone': row.get('client__phone'),
                })(),
                'total_revenue': row['total_revenue'],
                'total_deals': row['deals_count'],
                'avg_check': (row['total_revenue'] / row['deals_count']) if row['deals_count'] else Decimal('0'),
            }
            for row in raw_top20 if row['client__id']
        ]
        
        # По количеству заказов — переиспользуем raw_top20, пересортировав
        top_20_clients_by_count = sorted(top_20_clients_by_revenue, key=lambda x: x['total_deals'], reverse=True)[:20]
        
        # По прибыли — быстрый расчет прибыли по клиентам
        profit_rows = list(
            DealItem.objects.filter(deal__status='paid').filter(top20_date_filter_q)
            .values('deal__client__id')
            .annotate(
                total_profit=Sum(
                    F('total_price') - F('width_meters') * Case(
                        When(fixed_cost_price__isnull=False, then=F('fixed_cost_price')),
                        default=F('fabric_color__fabric__cost_price'),
                        output_field=models.DecimalField()
                    ),
                    output_field=models.DecimalField()
                )
            )
            .order_by('-total_profit')[:20]
        )
        profit_by_client = {r['deal__client__id']: r['total_profit'] for r in profit_rows}
        
        top_20_clients_by_profit = [
            {
                'client': clients_by_id.get(row['client__id']) or type('obj', (object,), {
                    'id': row['client__id'],
                    'nickname': row['client__nickname'],
                    'phone': row.get('client__phone'),
                })(),
                'total_profit': profit_by_client.get(row['client__id']) or Decimal('0'),
                'margin': float((profit_by_client.get(row['client__id']) or Decimal('0')) / row['total_revenue'] * 100) if row['total_revenue'] else 0.0,
            }
            for row in raw_top20 if row['client__id']
        ]
        top_20_clients_by_profit.sort(key=lambda x: x['total_profit'], reverse=True)

        # Топ-20 тканей
        fabric_qs_base = DealItem.objects.filter(deal__status='paid', fabric_color__fabric__isnull=False).filter(top20_date_filter_q)

        # По количеству заказов
        orders_rows = list(
            fabric_qs_base
            .values('fabric_color__fabric__id')
            .annotate(
                total_orders=Count('deal', distinct=True),
                order_frequency=Count('id')
            )
            .order_by('-total_orders')[:20]
        )
        fabric_ids_orders = [r['fabric_color__fabric__id'] for r in orders_rows if r['fabric_color__fabric__id']]

        # По метрам
        meters_rows = list(
            fabric_qs_base
            .values('fabric_color__fabric__id')
            .annotate(
                total_meters=Sum('width_meters'),
                total_orders=Count('deal', distinct=True)
            )
            .order_by('-total_meters')[:20]
        )
        fabric_ids_meters = [r['fabric_color__fabric__id'] for r in meters_rows if r['fabric_color__fabric__id']]

        # По прибыли/выручке
        profit_rows_fabric = list(
            fabric_qs_base
            .values('fabric_color__fabric__id')
            .annotate(
                total_revenue=Sum('total_price'),
                total_profit=Sum(
                    F('total_price') - F('width_meters') * Case(
                        When(fixed_cost_price__isnull=False, then=F('fixed_cost_price')),
                        default=F('fabric_color__fabric__cost_price'),
                        output_field=models.DecimalField()
                    ),
                    output_field=models.DecimalField()
                )
            )
            .order_by('-total_profit')[:20]
        )
        fabric_ids_profit = [r['fabric_color__fabric__id'] for r in profit_rows_fabric if r['fabric_color__fabric__id']]

        # Собираем объекты тканей
        fabric_ids = list({*fabric_ids_orders, *fabric_ids_meters, *fabric_ids_profit})
        fabrics_by_id = {f.id: f for f in Fabric.objects.filter(id__in=fabric_ids)}

        # Формируем структуры для шаблона
        top_20_fabrics_by_orders = [
            {
                'fabric': fabrics_by_id.get(r['fabric_color__fabric__id']),
                'total_orders': r['total_orders'],
                'order_frequency': r['order_frequency'],
            }
            for r in orders_rows if r['fabric_color__fabric__id'] and fabrics_by_id.get(r['fabric_color__fabric__id'])
        ]

        top_20_fabrics_by_meters = [
            {
                'fabric': fabrics_by_id.get(r['fabric_color__fabric__id']),
                'total_meters': r['total_meters'] or 0,
                'total_orders': r['total_orders'],
            }
            for r in meters_rows if r['fabric_color__fabric__id'] and fabrics_by_id.get(r['fabric_color__fabric__id'])
        ]

        top_20_fabrics_by_profit = [
            {
                'fabric': fabrics_by_id.get(r['fabric_color__fabric__id']),
                'total_profit': r['total_profit'] or Decimal('0'),
                'total_revenue': r['total_revenue'] or Decimal('0'),
            }
            for r in profit_rows_fabric if r['fabric_color__fabric__id'] and fabrics_by_id.get(r['fabric_color__fabric__id'])
        ]

    # Данные о периоде
    period_deals = Deal.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status='paid'
    ).order_by('-created_at')[:50]  # Ограничиваем для производительности
    
    period_revenue = period_deals.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0')
    period_profit = calculate_profit_optimized(
        Q(deal__created_at__date__gte=date_from) & Q(deal__created_at__date__lte=date_to)
    )
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
        'current_period_rolls_count': current_period_rolls_count,
        'current_period_cost': current_period_revenue - current_period_profit,
        
        # Тренды
        'revenue_trend': revenue_trend,
        'profit_trend': profit_trend,
        'margin_trend': margin_trend,
        'avg_check_trend': avg_check_trend,
        'deals_count_trend': deals_count_trend,
        'rolls_count_trend': rolls_count_trend,
        
        # Быстрые периоды
        'today_revenue': today_revenue,
        'today_deals_count': today_deals_count,
        'week_revenue': week_revenue,
        'week_deals_count': week_deals_count,
        'month_revenue': month_revenue,
        'month_deals_count': month_deals_count,
        'quarter_revenue': quarter_revenue,
        'quarter_deals_count': quarter_deals_count,
        'year_revenue': year_revenue,
        'year_deals_count': year_deals_count,
        
        'today_iso': today.strftime('%Y-%m-%d'),
        'week_start_iso': week_start.strftime('%Y-%m-%d'),
        'month_start_iso': month_start.strftime('%Y-%m-%d'),
        'quarter_start_iso': quarter_start.strftime('%Y-%m-%d'),
        'year_start_iso': year_start.strftime('%Y-%m-%d'),
        
        # Форматированные даты для отображения периодов
        'today_display': today.strftime('%d.%m.%Y'),
        'week_display': f"{week_start.strftime('%d.%m.%Y')} - {today.strftime('%d.%m.%Y')}",
        'month_display': f"{month_start.strftime('%d.%m.%Y')} - {today.strftime('%d.%m.%Y')}",
        'quarter_display': f"{quarter_start.strftime('%d.%m.%Y')} - {today.strftime('%d.%m.%Y')}",
        'year_display': f"{year_start.strftime('%d.%m.%Y')} - {today.strftime('%d.%m.%Y')}",

        # Отображение текущего периода для заголовка KPI
        'current_period_display': f"{current_period_start.strftime('%d.%m.%Y')} - {current_period_end.strftime('%d.%m.%Y')}",

        # Топ-ткань месяца
        'top_fabric_month': top_fabric_month,
        
        # Оборачиваемость
        'turnover_days': turnover_days,
        
        # Топ-клиенты
        'top_clients_by_profit': top_clients_by_profit,
        'top_clients_by_count': top_clients_by_count,
        'top_clients_by_sum': top_clients_by_sum,
        
        # Топ-ткани
        'top_fabrics_by_meters': top_fabrics_by_meters,
        'top_fabrics_by_profit': top_fabrics_by_profit,
        'top_fabrics_by_revenue': top_fabrics_by_revenue,
        
        # Топ 20 (только для админа)
        'top_20_clients_by_revenue': top_20_clients_by_revenue,
        'top_20_clients_by_count': top_20_clients_by_count,
        'top_20_clients_by_profit': top_20_clients_by_profit,
        'top_20_fabrics_by_orders': top_20_fabrics_by_orders,
        'top_20_fabrics_by_meters': top_20_fabrics_by_meters,
        'top_20_fabrics_by_profit': top_20_fabrics_by_profit,
        
        # Данные для периода
        'date_from': date_from,
        'date_to': date_to,
        'period_revenue': period_revenue,
        'period_profit': period_profit,
        'period_margin': period_margin,
        'period_deals_count': period_deals_count,
        'period_avg_check': period_avg_check,
        'period_deals': period_deals,
        
        # Данные для графиков
        'weekly_revenue': weekly_revenue,
        'week_labels': week_labels,

        # Параметры Top-20 для шаблона
        'top20_mode': top20_mode,
        'top20_month_from': top20_month_from,
        'top20_month_to': top20_month_to,
        'top20_year_from': top20_year_from,
        'top20_year_to': top20_year_to,
    }
    
    # Кешируем на 5 минут
    cache.set(cache_key, context, 300)
    
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
            
            # Сохраняем пароль в pass.txt файл
            import os
            from datetime import datetime
            
            # Путь к файлу pass.txt в корне проекта
            project_root = os.path.dirname(os.path.dirname(__file__))
            password_file = os.path.join(project_root, 'pass.txt')
            
            # Записываем пароль в файл
            with open(password_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                role_display = user_to_recreate.userprofile.get_role_display() if hasattr(user_to_recreate, 'userprofile') else 'Неизвестная роль'
                f.write(f'{timestamp} - Пользователь {user_to_recreate.username} ({role_display}) - ПЕРЕСОЗДАН: {new_password}\n')
            
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
            from django.contrib.auth import authenticate
            
            user_id = request.POST.get('user_id')
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not user_id or not old_password or not new_password or not confirm_password:
                return JsonResponse({'success': False, 'error': 'Не указаны обязательные параметры'})
            
            if new_password != confirm_password:
                return JsonResponse({'success': False, 'error': 'Новые пароли не совпадают'})
            
            user_to_update = User.objects.get(id=user_id)
            
            # Запрещаем изменять пароль самого админа
            if user_to_update.id == request.user.id:
                return JsonResponse({'success': False, 'error': 'Нельзя изменять свой пароль через эту функцию'})
            
            # Проверяем старый пароль
            if not user_to_update.check_password(old_password):
                return JsonResponse({'success': False, 'error': 'Неверный старый пароль'})
            
            user_to_update.set_password(new_password)
            user_to_update.save()
            
            # Сохраняем пароль в pass.txt файл
            import os
            from datetime import datetime
            
            # Путь к файлу pass.txt в корне проекта
            project_root = os.path.dirname(os.path.dirname(__file__))
            password_file = os.path.join(project_root, 'pass.txt')
            
            # Записываем пароль в файл
            with open(password_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f'{timestamp} - Пользователь {user_to_update.username} ({user_to_update.userprofile.get_role_display()}): {new_password}\n')
            
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
        
        # Сохраняем пароль в pass.txt файл
        import os
        from datetime import datetime
        
        # Путь к файлу pass.txt в корне проекта
        project_root = os.path.dirname(os.path.dirname(__file__))
        password_file = os.path.join(project_root, 'pass.txt')
        
        # Записываем пароль в файл
        with open(password_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            role_display = user.userprofile.get_role_display() if hasattr(user, 'userprofile') else 'Неизвестная роль'
            f.write(f'{timestamp} - Пользователь {user.username} ({role_display}): {new_password}\n')
        
        return JsonResponse({'success': True, 'message': f'Пароль для пользователя {user.username} успешно изменен'})
    
    except User.DoesNotExist:
        return JsonResponse({'error': 'Пользователь не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Ошибка при смене пароля: {str(e)}'}, status=500)


@login_required
@require_POST
def change_admin_password(request):
    """Смена пароля администратора с сохранением в txt файл"""
    if request.user.userprofile.role != 'admin':
        return JsonResponse({'success': False, 'error': 'Нет прав для выполнения операции'})
    
    if request.method == 'POST':
        try:
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not old_password or not new_password or not confirm_password:
                return JsonResponse({'success': False, 'error': 'Не указаны обязательные параметры'})
            
            if new_password != confirm_password:
                return JsonResponse({'success': False, 'error': 'Новые пароли не совпадают'})
            
            # Проверяем старый пароль
            if not request.user.check_password(old_password):
                return JsonResponse({'success': False, 'error': 'Неверный старый пароль'})
            
            # Изменяем пароль текущего админа
            request.user.set_password(new_password)
            request.user.save()
            
            # Сохраняем пароль в pass.txt файл
            import os
            from datetime import datetime
            
            # Путь к файлу pass.txt в корне проекта
            project_root = os.path.dirname(os.path.dirname(__file__))
            password_file = os.path.join(project_root, 'pass.txt')
            
            # Записываем пароль в файл
            with open(password_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f'{timestamp} - Администратор {request.user.username}: {new_password}\n')
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})


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

    today = timezone.localdate()

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


@login_required
def change_user_password_page(request):
    """Страница для смены пароля пользователей (только для админа)"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return redirect('core:home')
    
    from django.contrib.auth.models import User
    from core.models import UserProfile
    
    # Получаем всех пользователей с их ролями, исключая текущего администратора
    users = []
    for user in User.objects.all():
        try:
            profile = user.userprofile
            # Исключаем текущего администратора из списка
            if user.id != request.user.id:
                users.append({
                    'id': user.id,
                    'username': user.username,
                    'role': profile.get_role_display(),
                    'role_code': profile.role
                })
        except UserProfile.DoesNotExist:
            continue
    
    context = {
        'users': users
    }
    return render(request, 'finances/change_user_password.html', context)


@login_required
def change_admin_password_page(request):
    """Страница для смены пароля администратора"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return redirect('core:home')
    
    return render(request, 'finances/change_admin_password.html')


@login_required
def get_top20_data(request):
    """Возвращает Top 20 клиентов и тканей по выбранному диапазону месяцев или годов в JSON."""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)

    today = timezone.localdate()
    top20_mode = request.GET.get('top20_mode', 'month')
    default_month = today.strftime('%Y-%m')
    default_year = today.strftime('%Y')

    top20_month_from = request.GET.get('top20_month_from', default_month)
    top20_month_to = request.GET.get('top20_month_to', default_month)
    top20_year_from = request.GET.get('top20_year_from', default_year)
    top20_year_to = request.GET.get('top20_year_to', default_year)

    try:
        if top20_mode == 'year':
            y_from = int(top20_year_from)
            y_to = int(top20_year_to)
            if y_from > y_to:
                y_from, y_to = y_to, y_from
            start_date = datetime(y_from, 1, 1).date()
            end_date = datetime(y_to, 12, 31).date()
        else:
            y1, m1 = map(int, top20_month_from.split('-'))
            y2, m2 = map(int, top20_month_to.split('-'))
            d1 = datetime(y1, m1, 1).date()
            last_day_m2 = calendar.monthrange(y2, m2)[1]
            d2 = datetime(y2, m2, last_day_m2).date()
            if d1 > d2:
                d1, d2 = d2, d1
            start_date, end_date = d1, d2
    except Exception:
        return JsonResponse({'error': 'Неверные параметры периода'}, status=400)

    date_q = Q(deal__created_at__date__gte=start_date) & Q(deal__created_at__date__lte=end_date)

    # Клиенты: выручка и кол-во
    raw_clients = list(
        Deal.objects.filter(status='paid', created_at__date__gte=start_date, created_at__date__lte=end_date)
        .values('client__id', 'client__nickname', 'client__phone')
        .annotate(total_revenue=Sum('total_amount'), deals_count=Count('id'))
        .order_by('-total_revenue')[:20]
    )
    client_ids = [r['client__id'] for r in raw_clients if r['client__id']]
    clients_by_id = {c.id: c for c in Client.objects.filter(id__in=client_ids)}

    clients_by_revenue = [
        {
            'id': r['client__id'],
            'nickname': (clients_by_id.get(r['client__id']).nickname if clients_by_id.get(r['client__id']) else r['client__nickname']) if r['client__id'] else '—',
            'phone': (clients_by_id.get(r['client__id']).phone if clients_by_id.get(r['client__id']) else r.get('client__phone')) if r['client__id'] else None,
            'total_revenue': float(r['total_revenue'] or 0),
            'total_deals': r['deals_count'],
            'avg_check': float((r['total_revenue'] / r['deals_count']) if r['deals_count'] else 0),
        }
        for r in raw_clients if r['client__id']
    ]

    # Клиенты: прибыль
    profit_rows = list(
        DealItem.objects.filter(deal__status='paid').filter(date_q)
        .values('deal__client__id')
        .annotate(
            total_profit=Sum(
                F('total_price') - F('width_meters') * Case(
                    When(fixed_cost_price__isnull=False, then=F('fixed_cost_price')),
                    default=F('fabric_color__fabric__cost_price'),
                    output_field=models.DecimalField()
                ),
                output_field=models.DecimalField()
            )
        )
        .order_by('-total_profit')[:20]
    )
    profit_by_client = {r['deal__client__id']: float(r['total_profit'] or 0) for r in profit_rows}
    clients_by_profit = [
        {
            'id': r['id'],
            'nickname': r['nickname'],
            'phone': r['phone'],
            'total_profit': float(profit_by_client.get(r['id'], 0)),
            'margin': float((profit_by_client.get(r['id'], 0) / r['total_revenue'] * 100) if r['total_revenue'] else 0),
        }
        for r in clients_by_revenue
    ]
    clients_by_profit.sort(key=lambda x: x['total_profit'], reverse=True)

    # Ткани
    fabric_qs = DealItem.objects.filter(deal__status='paid', fabric_color__fabric__isnull=False).filter(date_q)

    fabrics_orders = list(
        fabric_qs.values('fabric_color__fabric__id')
        .annotate(total_orders=Count('deal', distinct=True), order_frequency=Count('id'))
        .order_by('-total_orders')[:20]
    )
    fabrics_meters = list(
        fabric_qs.values('fabric_color__fabric__id')
        .annotate(total_meters=Sum('width_meters'), total_orders=Count('deal', distinct=True))
        .order_by('-total_meters')[:20]
    )
    fabrics_profit = list(
        fabric_qs.values('fabric_color__fabric__id')
        .annotate(
            total_revenue=Sum('total_price'),
            total_profit=Sum(
                F('total_price') - F('width_meters') * Case(
                    When(fixed_cost_price__isnull=False, then=F('fixed_cost_price')),
                    default=F('fabric_color__fabric__cost_price'),
                    output_field=models.DecimalField()
                ),
                output_field=models.DecimalField()
            )
        )
        .order_by('-total_profit')[:20]
    )

    fabric_ids = list({*(r['fabric_color__fabric__id'] for r in fabrics_orders), *(r['fabric_color__fabric__id'] for r in fabrics_meters), *(r['fabric_color__fabric__id'] for r in fabrics_profit)})
    fabrics_by_id = {f.id: f for f in Fabric.objects.filter(id__in=fabric_ids)}

    fabrics_orders_out = [
        {
            'id': fid,
            'name': fabrics_by_id[fid].name if fid in fabrics_by_id else '—',
            'total_orders': r['total_orders'],
            'order_frequency': r['order_frequency'],
        }
        for r in fabrics_orders if (fid := r['fabric_color__fabric__id']) and fid in fabrics_by_id
    ]

    fabrics_meters_out = [
        {
            'id': fid,
            'name': fabrics_by_id[fid].name if fid in fabrics_by_id else '—',
            'total_meters': float(r['total_meters'] or 0),
            'total_orders': r['total_orders'],
        }
        for r in fabrics_meters if (fid := r['fabric_color__fabric__id']) and fid in fabrics_by_id
    ]

    fabrics_profit_out = [
        {
            'id': fid,
            'name': fabrics_by_id[fid].name if fid in fabrics_by_id else '—',
            'total_profit': float(r['total_profit'] or 0),
            'total_revenue': float(r['total_revenue'] or 0),
        }
        for r in fabrics_profit if (fid := r['fabric_color__fabric__id']) and fid in fabrics_by_id
    ]

    return JsonResponse({
        'clients': {
            'revenue': clients_by_revenue,
            'count': sorted(clients_by_revenue, key=lambda x: x['total_deals'], reverse=True)[:20],
            'profit': clients_by_profit,
        },
        'fabrics': {
            'orders': fabrics_orders_out,
            'meters': fabrics_meters_out,
            'profit': fabrics_profit_out,
        }
    })

