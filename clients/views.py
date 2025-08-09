from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count, Avg
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta
from .models import Client
from .forms import ClientForm
from core.models import ActivityLog


@login_required
def client_list(request):
    """Список всех клиентов"""
    try:
        search_query = request.GET.get('search', '')
        
        clients = Client.objects.all().order_by('-created_at')
        if search_query:
            clients = clients.filter(
                Q(nickname__icontains=search_query) |
                Q(full_name__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(notes__icontains=search_query)
            )
        
        context = {
            'clients': clients,
            'search_query': search_query,
        }
        return render(request, 'clients/client_list.html', context)
    except Exception as e:
        print(f"Ошибка в client_list: {e}")
        messages.error(request, f"Произошла ошибка при загрузке списка клиентов: {e}")
        return render(request, 'clients/client_list.html', {'clients': [], 'search_query': ''})


@login_required
def client_search_ajax(request):
    """AJAX endpoint для поиска клиентов"""
    try:
        search_query = request.GET.get('search', '')
        
        clients = Client.objects.all().order_by('-created_at')
        if search_query:
            clients = clients.filter(
                Q(nickname__icontains=search_query) |
                Q(full_name__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(notes__icontains=search_query)
            )
        
        # Подготавливаем данные для JSON ответа
        clients_data = []
        for client in clients:
            last_deal = client.deal_set.first()
            clients_data.append({
                'id': client.id,
                'nickname': client.nickname,
                'full_name': client.full_name or '',
                'phone': client.phone or 'Не указан',
                'notes': client.notes or '',
                'deals_count': client.deal_set.count(),
                'last_deal_number': last_deal.deal_number if last_deal else None,
                'last_deal_id': last_deal.id if last_deal else None,
                'created_at': client.created_at.strftime('%d.%m.%Y') if client.created_at else '',
            })
        
        return JsonResponse({
            'success': True,
            'clients': clients_data,
            'count': len(clients_data),
            'query': search_query
        })
        
    except Exception as e:
        print(f"Ошибка в client_search_ajax: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'clients': [],
            'count': 0
        })


@login_required
def client_detail(request, client_id):
    """Детальная информация о клиенте"""
    client = get_object_or_404(Client, id=client_id)
    
    # Получаем параметры фильтрации
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Получаем заказы клиента
    deals = client.deal_set.all().order_by('-created_at')
    
    # Фильтруем по датам если указаны
    if date_from:
        deals = deals.filter(created_at__date__gte=date_from)
    if date_to:
        deals = deals.filter(created_at__date__lte=date_to)
    
    # Статистика по всем заказам клиента
    total_deals = client.deal_set.count()
    total_revenue = client.deal_set.filter(status='paid').aggregate(total=Sum('total_amount'))['total'] or 0
    total_profit = 0
    for deal in client.deal_set.filter(status='paid'):
        total_profit += deal.total_profit
    
    # Статистика по отфильтрованным заказам
    filtered_deals_count = deals.count()
    filtered_revenue = deals.filter(status='paid').aggregate(total=Sum('total_amount'))['total'] or 0
    filtered_profit = 0
    for deal in deals.filter(status='paid'):
        filtered_profit += deal.total_profit
    
    # Средний чек
    avg_check = deals.filter(status='paid').aggregate(avg=Avg('total_amount'))['avg'] or 0
    
    # Даты для быстрых фильтров
    today = timezone.now().date()
    today_iso = today.isoformat()
    
    # Неделя назад
    week_ago = today - timedelta(days=7)
    week_start_iso = week_ago.isoformat()
    
    # Месяц назад
    month_ago = today - timedelta(days=30)
    month_start_iso = month_ago.isoformat()
    
    # Квартал назад
    quarter_ago = today - timedelta(days=90)
    quarter_start_iso = quarter_ago.isoformat()
    
    # Год назад
    year_ago = today - timedelta(days=365)
    year_start_iso = year_ago.isoformat()
    
    context = {
        'client': client,
        'deals': deals,
        'total_deals': total_deals,
        'total_revenue': total_revenue,
        'total_profit': total_profit,
        'filtered_deals_count': filtered_deals_count,
        'filtered_revenue': filtered_revenue,
        'filtered_profit': filtered_profit,
        'avg_check': avg_check,
        'date_from': date_from or today_iso,
        'date_to': date_to or today_iso,
        'today_iso': today_iso,
        'week_start_iso': week_start_iso,
        'month_start_iso': month_start_iso,
        'quarter_start_iso': quarter_start_iso,
        'year_start_iso': year_start_iso,
    }
    return render(request, 'clients/client_detail.html', context)


@login_required
def client_create(request):
    """Создание нового клиента"""
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            
            # Логирование
            ActivityLog.objects.create(
                user=request.user,
                action='create',
                object_type='Client',
                object_id=client.id,
                description=f'Создан клиент: {client.nickname}'
            )
            
            messages.success(request, f'Клиент "{client.nickname}" успешно создан.')
            return redirect('clients:client_detail', client_id=client.id)
    else:
        form = ClientForm()
    
    return render(request, 'clients/client_form.html', {'form': form, 'title': 'Создать клиента'})


@login_required
def client_edit(request, client_id):
    """Редактирование клиента"""
    client = get_object_or_404(Client, id=client_id)
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            client = form.save()
            
            # Логирование
            ActivityLog.objects.create(
                user=request.user,
                action='update',
                object_type='Client',
                object_id=client.id,
                description=f'Отредактирован клиент: {client.nickname}'
            )
            
            messages.success(request, f'Клиент "{client.nickname}" успешно обновлен.')
            return redirect('clients:client_detail', client_id=client.id)
    else:
        form = ClientForm(instance=client)
    
    return render(request, 'clients/client_form.html', {'form': form, 'title': 'Редактировать клиента'})


@login_required
@require_POST
def client_delete(request, client_id):
    """Удаление клиента (только для админа)"""
    if request.user.userprofile.role != 'admin':
        return JsonResponse({'error': 'Нет прав доступа'}, status=403)
    
    client = get_object_or_404(Client, id=client_id)
    client_name = client.nickname
    
    # Проверяем, есть ли у клиента сделки
    if client.deal_set.exists():
        return JsonResponse({'error': 'Нельзя удалить клиента, у которого есть сделки'}, status=400)
    
    # Логирование
    ActivityLog.objects.create(
        user=request.user,
        action='delete',
        object_type='Client',
        object_id=client.id,
        description=f'Удален клиент: {client_name}'
    )
    
    # Удаляем клиента
    client.delete()
    
    return JsonResponse({'success': True})

