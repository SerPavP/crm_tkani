from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import JsonResponse
from fabrics.models import FabricRoll
from .forms import CreateBarcodeForm, ScanBarcodeForm
from fabrics.models import FabricColor
from core.models import ActivityLog
import random
import string
import barcode
from barcode.writer import ImageWriter, SVGWriter
from barcode import Code128, Code39, EAN13
from pyzbar.pyzbar import decode
from pyzbar import pyzbar
from PIL import Image
import io
import base64
from io import BytesIO




@login_required
def manage_rolls(request):
    """Управление рулонами для администратора/бухгалтера/складовщика"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role not in ['admin', 'accountant', 'warehouse']:
        messages.error(request, 'У вас нет прав для управления рулонами.')
        return redirect('core:home')

    search_query = request.GET.get('search', '')
    fabric_filter = request.GET.get('fabric', '')
    status_filter = request.GET.get('status', '')

    rolls = FabricRoll.objects.select_related('fabric_color__fabric').all()

    if search_query:
        rolls = rolls.filter(
            Q(barcode__icontains=search_query) |
            Q(fabric_color__fabric__name__icontains=search_query) |
            Q(fabric_color__color_name__icontains=search_query)
        )

    if fabric_filter:
        rolls = rolls.filter(fabric_color__fabric__id=fabric_filter)

    if status_filter == 'active':
        rolls = rolls.filter(is_active=True)
    elif status_filter == 'inactive':
        rolls = rolls.filter(is_active=False)

    rolls = rolls.order_by('-created_at')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            form = CreateBarcodeForm(request.POST)
            if form.is_valid():
                fabric_color = form.cleaned_data['fabric_color']
                width_meters = form.cleaned_data['width_meters']

                # Генерация штрих-кода
                barcode = generate_barcode()

                fabric_roll = FabricRoll.objects.create(
                    fabric_color=fabric_color,
                    width_meters=width_meters,
                    barcode=barcode,
                )

                # Логирование
                ActivityLog.objects.create(
                    user=request.user,
                    action='create',
                    object_type='FabricRoll',
                    object_id=fabric_roll.id,
                    description=f'Добавлен рулон {fabric_roll.barcode} вручную'
                )

                messages.success(request, f'Рулон {fabric_roll.barcode} успешно добавлен.')
            else:
                messages.error(request, 'Ошибка при добавлении рулона.')

        elif action == 'delete':
            roll_id = request.POST.get('roll_id')
            roll = get_object_or_404(FabricRoll, id=roll_id)

            # Логирование
            ActivityLog.objects.create(
                user=request.user,
                action='delete',
                object_type='FabricRoll',
                object_id=roll.id,
                description=f'Удален рулон {roll.barcode} вручную'
            )

            roll.delete()
            messages.success(request, 'Рулон успешно удален.')

        elif action == 'toggle_status':
            roll_id = request.POST.get('roll_id')
            roll = get_object_or_404(FabricRoll, id=roll_id)
            roll.is_active = not roll.is_active
            roll.save()

            # Логирование
            status_text = 'активирован' if roll.is_active else 'деактивирован'
            ActivityLog.objects.create(
                user=request.user,
                action='update',
                object_type='FabricRoll',
                object_id=roll.id,
                description=f'Рулон {roll.barcode} {status_text}'
            )

            messages.success(request, f'Рулон {status_text}.')

        return redirect('warehouse:manage_rolls')

    form = CreateBarcodeForm()
    fabrics = FabricColor.objects.select_related('fabric').values(
        'fabric__id', 'fabric__name'
    ).distinct()

    context = {
        'rolls': rolls,
        'form': form,
        'search_query': search_query,
        'fabric_filter': fabric_filter,
        'status_filter': status_filter,
        'fabrics': fabrics,
    }
    return render(request, 'warehouse/manage_rolls.html', context)


@login_required
def view_rolls(request):
    """Просмотр рулонов для складовщика"""
    search_query = request.GET.get('search', '')
    fabric_filter = request.GET.get('fabric', '')
    color_filter = request.GET.get('color', '')

    rolls = FabricRoll.objects.select_related('fabric_color__fabric').filter(is_active=True)

    if search_query:
        rolls = rolls.filter(barcode__icontains=search_query)

    if fabric_filter:
        rolls = rolls.filter(fabric_color__fabric__id=fabric_filter)

    if color_filter:
        rolls = rolls.filter(fabric_color__id=color_filter)

    rolls = rolls.order_by('-created_at')

    # Получаем уникальные ткани для фильтра (без дублирования)
    from fabrics.models import Fabric
    unique_fabrics = Fabric.objects.filter(
        fabriccolor__fabric_rolls_from_fabrics__is_active=True
    ).distinct().order_by('name')

    context = {
        'rolls': rolls,
        'search_query': search_query,
        'fabric_filter': fabric_filter,
        'color_filter': color_filter,
        'unique_fabrics': unique_fabrics,
    }
    return render(request, 'warehouse/view_rolls.html', context)


@login_required
def create_barcode(request):
    """Создание штрих-кода для складовщика"""
    if not request.user.userprofile.can_create_barcodes:
        messages.error(request, 'У вас нет прав для создания штрих-кодов.')
        return redirect('warehouse:view_rolls')
    
    form = 0
    if request.method == 'POST':
        fabric_color_id = request.POST.get('fabric_color')
        width_meters = request.POST.get('width_meters')
        
        if fabric_color_id and width_meters:
            try:
                fabric_color = FabricColor.objects.get(id=fabric_color_id)
                width_meters = float(width_meters)
                
                if width_meters <= 0:
                    messages.error(request, 'Ширина рулона должна быть больше 0.')
                    return redirect('warehouse:create_barcode')

                # Генерация штрих-кода
                barcode = generate_barcode()

                fabric_roll = FabricRoll.objects.create(
                    fabric_color=fabric_color,
                    width_meters=width_meters,
                    barcode=barcode,
                )

                # Логирование
                ActivityLog.objects.create(
                    user=request.user,
                    action='create',
                    object_type='FabricRoll',
                    object_id=fabric_roll.id,
                    description=f'Создан рулон {fabric_roll.barcode} складовщиком'
                )

                messages.success(request, f'Рулон {fabric_roll.barcode} успешно создан.')
                return redirect('warehouse:barcode_print', barcode=fabric_roll.barcode)
                
            except FabricColor.DoesNotExist:
                messages.error(request, 'Выбранный цвет ткани не найден.')
            except ValueError:
                messages.error(request, 'Некорректное значение ширины рулона.')
        else:
            messages.error(request, 'Пожалуйста, заполните все поля.')
    else:
        form = CreateBarcodeForm()

    # Получаем все ткани для выбора
    from fabrics.models import Fabric
    fabrics = Fabric.objects.all().order_by('name')

    # Получаем параметры для автозаполнения из URL
    fabric_id = request.GET.get('fabric_id')
    color_id = request.GET.get('color_id')
    
    selected_fabric = None
    selected_color = None
    
    if fabric_id:
        try:
            selected_fabric = Fabric.objects.get(id=fabric_id)
        except Fabric.DoesNotExist:
            pass
    
    if color_id:
        try:
            selected_color = FabricColor.objects.get(id=color_id)
            if selected_color:
                selected_fabric = selected_color.fabric
        except FabricColor.DoesNotExist:
            pass

    context = {
        'form': form,
        'fabrics': fabrics,
        'selected_fabric': selected_fabric,
        'selected_color': selected_color,
    }
    return render(request, 'warehouse/create_barcode.html', context)


@login_required
def scan_barcode(request):
    """Сканирование штрих-кода для списания"""
    from fabrics.models import Fabric
    fabrics = Fabric.objects.all().order_by('name')
    if request.method == 'POST':
        action = request.POST.get('action', 'scan')
        
        if action == 'scan':
            # Первый шаг - поиск рулона
            form = ScanBarcodeForm(request.POST)
            if form.is_valid():
                barcode = form.cleaned_data['barcode']

                try:
                    roll = FabricRoll.objects.get(barcode=barcode, is_active=True)
                    return render(request, 'warehouse/scan_barcode.html', {
                        'form': ScanBarcodeForm(),
                        'found_roll': roll,  # Рулон найден, показываем подтверждение
                        'confirm_barcode': barcode,
                        'fabrics': fabrics,
                    })

                except FabricRoll.DoesNotExist:
                    messages.error(request, 'Рулон с таким штрих-кодом не найден или уже списан.')
                    
        elif action == 'confirm':
            # Второй шаг - подтверждение списания
            barcode = request.POST.get('confirm_barcode')
            
            try:
                roll = FabricRoll.objects.get(barcode=barcode, is_active=True)

                # Деактивируем рулон (списываем)
                roll.is_active = False
                roll.save()

                # Логирование
                ActivityLog.objects.create(
                    user=request.user,
                    action='update',
                    object_type='FabricRoll',
                    object_id=roll.id,
                    description=f'Рулон {roll.barcode} списан через сканирование'
                )

                messages.success(request, f'Рулон {roll.barcode} успешно списан со склада.')
                return render(request, 'warehouse/scan_barcode.html', {
                    'form': ScanBarcodeForm(),
                    'scanned_roll': roll,  # Рулон списан, показываем результат
                    'fabrics': fabrics,
                })

            except FabricRoll.DoesNotExist:
                messages.error(request, 'Рулон с таким штрих-кодом не найден или уже списан.')
    else:
        form = ScanBarcodeForm()

    # Поддержка автозаполнения штрих-кода через GET
    barcode_prefill = request.GET.get('barcode', '')
    if barcode_prefill:
        form.fields['barcode'].initial = barcode_prefill

    return render(request, 'warehouse/scan_barcode.html', {'form': form, 'fabrics': fabrics, 'barcode_prefill': barcode_prefill})


# (pr2) Добавить view для генерации и печати QR/штрих-кода
@login_required
def scan_barcode_function_view(request):
    if request.method == 'POST':

        if 'image' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Изображение не найдено'
            })
        
        file = request.FILES['image']
        if file.name == '':
            return JsonResponse({
                'success': False,
                'error': 'No selected file'
                })
        try:
            img = Image.open(io.BytesIO(file.read()))
            img = img.convert('RGB')
            barcodes = decode(img)
            if barcodes:
            # Берем первый найденный штрих-код
                barcode = barcodes[0]
                barcode_data = barcode.data.decode('utf-8')
                
                return JsonResponse({
                    'success': True,
                    'barcode': barcode_data,
                    'type': barcode.type
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Штрих-код не найден на изображении'
                })
        except Exception as e:
            return JsonResponse({
                    'error': str(e)
                })


# Это может быть модификация barcode_print или отдельная функция для генерации PDF.
@login_required
def barcode_print(request, barcode):
    """Страница печати штрих-кода с улучшенными настройками качества"""
    roll = get_object_or_404(FabricRoll, barcode=barcode)
    
    # Генерация штрих-кода
    try:
        # Создаем штрих-код Code128
        code128 = Code128(barcode, writer=ImageWriter())
        
        # Создаем буфер для изображения
        buffer = BytesIO()
        
        # Оптимизированные настройки для принтера Xprinter XP-T371U (58мм x 40мм этикетки)
        barcode_options = {
            'module_width': 0.375,    # увеличенная ширина в 1.5 раза для лучшего сканирования
            'module_height': 22,      # увеличенная высота в 1.5 раза для четкости
            'quiet_zone': 7,          # увеличенная тихая зона для надежности
            'font_size': 15,          # увеличенный размер шрифта в 1.5 раза
            'text_distance': 3,       # расстояние до текста
            'background': 'white',    # белый фон
            'foreground': 'black',    # черные полосы
            'write_text': True,       # показывать текст под штрих-кодом
            'center_text': True,      # центрировать текст
            'dpi': 300,               # высокое разрешение для печати
        }
        
        # Генерируем изображение
        code128.write(buffer, options=barcode_options)
        
        # Дополнительная обработка изображения для улучшения качества
        buffer.seek(0)
        
        # Открываем изображение через PIL для дополнительной обработки
        img = Image.open(buffer)
        
        # Убеждаемся, что изображение в RGB режиме
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Увеличиваем изображение для лучшего качества при печати
        # Увеличиваем в 2 раза с использованием качественного алгоритма
        new_width = img.width * 2
        new_height = img.height * 2
        img_resized = img.resize((new_width, new_height), Image.LANCZOS)
        
        # Сохраняем обработанное изображение обратно в буфер
        final_buffer = BytesIO()
        img_resized.save(final_buffer, format='PNG', dpi=(300, 300), optimize=True)
        final_buffer.seek(0)
        
        # Кодируем в base64
        barcode_image = base64.b64encode(final_buffer.getvalue()).decode('utf-8')
        
        buffer.close()
        final_buffer.close()
        
    except Exception as e:
        # В случае ошибки генерации, используем базовые настройки
        print(f"Ошибка генерации штрих-кода: {e}")
        try:
            # Попытка с минимальными настройками
            code128 = Code128(barcode, writer=ImageWriter())
            buffer = BytesIO()
            code128.write(buffer, {
                'module_width': 0.3,
                'module_height': 12,
                'dpi': 200,
                'quiet_zone': 4,
            })
            buffer.seek(0)
            barcode_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            buffer.close()
        except:
            barcode_image = None
    
    context = {
        'roll': roll,
        'barcode': barcode,
        'barcode_image': barcode_image,
    }
    return render(request, 'warehouse/barcode_print.html', context)


@login_required
def delete_roll(request):
    """Удаление рулона безвозвратно"""
    barcode = request.GET.get('barcode')
    
    if not barcode:
        messages.error(request, 'Штрих-код не указан.')
        return redirect('warehouse:view_rolls')
    
    try:
        roll = FabricRoll.objects.get(barcode=barcode, is_active=True)
        
        # Логирование
        ActivityLog.objects.create(
            user=request.user,
            action='delete',
            object_type='FabricRoll',
            object_id=roll.id,
            description=f'Рулон {roll.barcode} удален безвозвратно складовщиком'
        )
        
        roll.delete()
        messages.success(request, f'Рулон {barcode} успешно удален безвозвратно.')
        
    except FabricRoll.DoesNotExist:
        messages.error(request, 'Рулон с таким штрих-кодом не найден.')
    
    return redirect('warehouse:view_rolls')


@login_required
def print_pending_barcodes(request):
    """Список штрих-кодов для печати (созданных админом/бухгалтером)"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'warehouse':
        messages.error(request, 'У вас нет прав для просмотра этой страницы.')
        return redirect('core:home')

    # Получаем рулоны, созданные не складовщиком (нужно распечатать)
    pending_rolls = FabricRoll.objects.filter(is_active=True).select_related('fabric_color__fabric')

    # Фильтруем по логам - рулоны, созданные админом или бухгалтером
    admin_created_rolls = []
    for roll in pending_rolls:
        log = ActivityLog.objects.filter(
            object_type='FabricRoll',
            object_id=roll.id,
            action='create'
        ).first()
        if log and hasattr(log.user, 'userprofile') and log.user.userprofile.role in ['admin', 'accountant']:
            admin_created_rolls.append(roll)

    context = {
        'pending_rolls': admin_created_rolls,
    }
    return render(request, 'warehouse/print_pending_barcodes.html', context)


@login_required
def get_fabric_colors_api(request):
    """API endpoint для получения цветов ткани"""
    fabric_id = request.GET.get('fabric_id')
    
    if not fabric_id:
        return JsonResponse({'colors': []})
    
    try:
        colors = FabricColor.objects.filter(fabric_id=fabric_id).values('id', 'color_name', 'color_number')
        colors_list = [
            {
                'id': color['id'],
                'name': color['color_name'],
                'number': color['color_number']
            }
            for color in colors
        ]
        return JsonResponse({'colors': colors_list})
    except:
        return JsonResponse({'colors': []})


def generate_barcode():
    """Генерация уникального 7-значного штрих-кода"""
    while True:
        barcode = '{:07d}'.format(random.randint(0, 9999999))
        if not FabricRoll.objects.filter(barcode=barcode).exists():
            return barcode

@login_required
def get_rolls_by_color_api(request):
    """API endpoint для получения рулонов по цвету (только активные)"""
    color_id = request.GET.get('color_id')
    if not color_id:
        return JsonResponse({'rolls': []})
    rolls = FabricRoll.objects.filter(fabric_color_id=color_id, is_active=True)
    rolls_list = [
        {
            'barcode': roll.barcode,
            'width_meters': float(roll.width_meters)
        } for roll in rolls
    ]
    return JsonResponse({'rolls': rolls_list})


@login_required
def search_barcodes_api(request):
    """API endpoint для поиска штрих-кодов по подстроке (только активные)"""
    q = request.GET.get('q', '').strip()
    if not q or len(q) < 2:
        return JsonResponse({'barcodes': []})
    barcodes = list(FabricRoll.objects.filter(barcode__icontains=q, is_active=True).order_by('-created_at').values_list('barcode', flat=True)[:10])
    return JsonResponse({'barcodes': barcodes})

