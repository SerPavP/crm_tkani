from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Fabric, FabricColor, FabricRoll
from .forms import FabricForm, FabricColorForm
from core.models import ActivityLog


@login_required
def fabric_list(request):
    """Список всех тканей"""
    search_query = request.GET.get('search', '')
    
    fabrics = Fabric.objects.all()
    if search_query:
        fabrics = fabrics.filter(
            Q(name__icontains=search_query) |
            Q(fabriccolor__color_number__icontains=search_query)
        ).distinct()
    
    # Сортируем: сначала ткани с рулонами, потом по коду цвета
    
    fabrics_with_rolls = []
    fabrics_without_rolls = []
    
    for fabric in fabrics:
        has_rolls = FabricRoll.objects.filter(
            fabric_color__fabric=fabric, 
            is_active=True
        ).exists()
        
        if has_rolls:
            fabrics_with_rolls.append(fabric)
        else:
            fabrics_without_rolls.append(fabric)
    
    # Сортируем каждую группу по коду цвета
    fabrics_with_rolls.sort(key=lambda x: int(x.fabriccolor_set.first().color_number) if x.fabriccolor_set.exists() and x.fabriccolor_set.first().color_number.isdigit() else 9999)
    fabrics_without_rolls.sort(key=lambda x: int(x.fabriccolor_set.first().color_number) if x.fabriccolor_set.exists() and x.fabriccolor_set.first().color_number.isdigit() else 9999)
    
    # Объединяем списки
    sorted_fabrics = fabrics_with_rolls + fabrics_without_rolls
    
    context = {
        'fabrics': sorted_fabrics,
        'search_query': search_query,
    }
    return render(request, 'fabrics/fabric_list.html', context)


@login_required
def fabric_detail(request, fabric_id):
    """Детальная информация о ткани с цветами"""
    fabric = get_object_or_404(Fabric, id=fabric_id)
    
    # Сортируем цвета: сначала с рулонами, потом по номеру цвета
    
    colors_with_rolls = []
    colors_without_rolls = []
    
    for color in fabric.fabriccolor_set.all():
        has_rolls = FabricRoll.objects.filter(
            fabric_color=color, 
            is_active=True
        ).exists()
        
        if has_rolls:
            colors_with_rolls.append(color)
        else:
            colors_without_rolls.append(color)
    
    # Сортируем каждую группу по номеру цвета
    colors_with_rolls.sort(key=lambda x: int(x.color_number) if x.color_number.isdigit() else 9999)
    colors_without_rolls.sort(key=lambda x: int(x.color_number) if x.color_number.isdigit() else 9999)
    
    # Объединяем списки
    sorted_colors = colors_with_rolls + colors_without_rolls
    
    context = {
        'fabric': fabric,
        'colors': sorted_colors,
    }
    return render(request, 'fabrics/fabric_detail.html', context)


@login_required
def fabric_create(request):
    """Создание новой ткани"""
    if not request.user.userprofile.can_view_finances:
        messages.error(request, 'У вас нет прав для создания тканей.')
        return redirect('fabrics:fabric_list')
    
    if request.method == 'POST':
        form = FabricForm(request.POST)
        if form.is_valid():
            fabric = form.save()
            
            # Логирование
            ActivityLog.objects.create(
                user=request.user,
                action='create',
                object_type='Fabric',
                object_id=fabric.id,
                description=f'Создана ткань: {fabric.name}'
            )
            
            messages.success(request, f'Ткань "{fabric.name}" успешно создана.')
            return redirect('fabrics:fabric_detail', fabric_id=fabric.id)
    else:
        form = FabricForm()
    
    return render(request, 'fabrics/fabric_form.html', {'form': form, 'title': 'Создать ткань'})


@login_required
def fabric_edit(request, fabric_id):
    """Редактирование ткани"""
    if not request.user.userprofile.can_view_finances:
        messages.error(request, 'У вас нет прав для редактирования тканей.')
        return redirect('fabrics:fabric_list')
    
    fabric = get_object_or_404(Fabric, id=fabric_id)
    
    if request.method == 'POST':
        form = FabricForm(request.POST, instance=fabric)
        if form.is_valid():
            fabric = form.save()
            
            # Логирование
            ActivityLog.objects.create(
                user=request.user,
                action='update',
                object_type='Fabric',
                object_id=fabric.id,
                description=f'Отредактирована ткань: {fabric.name}'
            )
            
            messages.success(request, f'Ткань "{fabric.name}" успешно обновлена.')
            return redirect('fabrics:fabric_detail', fabric_id=fabric.id)
    else:
        form = FabricForm(instance=fabric)
    
    return render(request, 'fabrics/fabric_form.html', {'form': form, 'title': 'Редактировать ткань'})


@login_required
def color_create(request, fabric_id):
    """Создание нового цвета для ткани"""
    if not request.user.userprofile.can_view_finances:
        messages.error(request, 'У вас нет прав для создания цветов.')
        return redirect('fabrics:fabric_list')
    
    fabric = get_object_or_404(Fabric, id=fabric_id)
    
    if request.method == 'POST':
        form = FabricColorForm(request.POST)
        if form.is_valid():
            color = form.save(commit=False)
            color.fabric = fabric
            color.save()
            
            # Логирование
            ActivityLog.objects.create(
                user=request.user,
                action='create',
                object_type='FabricColor',
                object_id=color.id,
                description=f'Создан цвет: {color.color_name} ({color.color_number}) для ткани {fabric.name}'
            )
            
            messages.success(request, f'Цвет "{color.color_name}" успешно добавлен.')
            return redirect('fabrics:fabric_detail', fabric_id=fabric.id)
    else:
        form = FabricColorForm()
    
    context = {
        'form': form,
        'fabric': fabric,
        'title': f'Добавить цвет для ткани "{fabric.name}"'
    }
    return render(request, 'fabrics/color_form.html', context)


@login_required
def color_edit(request, color_id):
    """Редактирование цвета ткани"""
    if not request.user.userprofile.can_view_finances:
        messages.error(request, 'У вас нет прав для редактирования цветов.')
        return redirect('fabrics:fabric_list')
    
    color = get_object_or_404(FabricColor, id=color_id)
    
    if request.method == 'POST':
        form = FabricColorForm(request.POST, instance=color)
        if form.is_valid():
            color = form.save()
            
            # Логирование
            ActivityLog.objects.create(
                user=request.user,
                action='update',
                object_type='FabricColor',
                object_id=color.id,
                description=f'Отредактирован цвет: {color.color_name} ({color.color_number}) для ткани {color.fabric.name}'
            )
            
            messages.success(request, f'Цвет "{color.color_name}" успешно обновлен.')
            return redirect('fabrics:fabric_detail', fabric_id=color.fabric.id)
    else:
        form = FabricColorForm(instance=color)
    
    context = {
        'form': form,
        'color': color,
        'title': f'Редактировать цвет "{color.color_name}"'
    }
    return render(request, 'fabrics/color_form.html', context)


@login_required
def get_fabric_colors(request, fabric_id):
    """API для получения цветов ткани (для AJAX)"""
    fabric = get_object_or_404(Fabric, id=fabric_id)
    colors = fabric.fabriccolor_set.all().values('id', 'color_name', 'color_number', 'price_per_meter')
    return JsonResponse({'colors': list(colors)})



@login_required
def get_colors_by_fabric(request):
    fabric_id = request.GET.get("fabric_id")
    colors = FabricColor.objects.filter(fabric_id=fabric_id).values("id", "color_name", "color_number")
    return JsonResponse(list(colors), safe=False)


@login_required
@require_POST
def fabric_delete(request, fabric_id):
    """Удаление ткани"""
    if not request.user.userprofile.can_view_finances:
        messages.error(request, 'У вас нет прав для удаления тканей.')
        return redirect('fabrics:fabric_list')
    
    fabric = get_object_or_404(Fabric, id=fabric_id)
    fabric_name = fabric.name
    
    # Подсчитываем количество связанных объектов
    deals_count = fabric.deals_count
    colors_count = fabric.fabriccolor_set.count()
    rolls_count = FabricRoll.objects.filter(fabric_color__fabric=fabric).count()
    
    try:
        # Удаляем ткань (каскадное удаление удалит все связанные объекты)
        fabric.delete()
        
        # Логирование
        ActivityLog.objects.create(
            user=request.user,
            action='delete',
            object_type='Fabric',
            object_id=fabric_id,
            description=f'Удалена ткань: {fabric_name} (цветов: {colors_count}, рулонов: {rolls_count}, сделок: {deals_count})'
        )
        
        messages.success(request, f'Ткань "{fabric_name}" успешно удалена.')
        if deals_count > 0:
            messages.warning(request, f'Внимание: было удалено {deals_count} позиций в сделках, связанных с этой тканью.')
        
    except Exception as e:
        messages.error(request, f'Ошибка при удалении ткани: {str(e)}')
    
    return redirect('fabrics:fabric_list')


@login_required
@require_POST
def color_delete(request, color_id):
    """Удаление цвета ткани"""
    if not request.user.userprofile.can_manage_fabrics:
        messages.error(request, 'У вас нет прав для удаления цветов.')
        return redirect('fabrics:fabric_list')
    
    color = get_object_or_404(FabricColor, id=color_id)
    fabric = color.fabric
    color_name = color.color_name
    color_number = color.color_number
    
    # Подсчитываем количество связанных объектов
    rolls_count = FabricRoll.objects.filter(fabric_color=color).count()
    active_rolls_count = FabricRoll.objects.filter(fabric_color=color, is_active=True).count()
    
    try:
        # Удаляем цвет (каскадное удаление удалит все связанные рулоны)
        color.delete()
        
        # Логирование
        ActivityLog.objects.create(
            user=request.user,
            action='delete',
            object_type='FabricColor',
            object_id=color_id,
            description=f'Удален цвет: {color_name} ({color_number}) для ткани {fabric.name} (рулонов: {rolls_count}, активных: {active_rolls_count})'
        )
        
        messages.success(request, f'Цвет "{color_name}" успешно удален.')
        if rolls_count > 0:
            messages.warning(request, f'Внимание: было удалено {rolls_count} рулонов этого цвета.')
        
    except Exception as e:
        messages.error(request, f'Ошибка при удалении цвета: {str(e)}')
    
    return redirect('fabrics:fabric_detail', fabric_id=fabric.id)

