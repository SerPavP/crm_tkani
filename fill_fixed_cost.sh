#!/bin/bash

# Скрипт для заполнения пустых fixed_cost_price
# Запуск: bash fill_fixed_cost.sh

echo "=== Заполнение пустых fixed_cost_price ==="
echo "Дата: $(date)"
echo ""

# Проверяем, существует ли база данных
if [ ! -f "db.sqlite3" ]; then
    echo "ОШИБКА: Файл db.sqlite3 не найден!"
    exit 1
fi

echo "Заполняем пустые fixed_cost_price из cost_price ткани..."
python manage.py shell -c "
from deals.models import DealItem
from django.db.models import Q

# Находим все записи с пустым fixed_cost_price
empty_items = DealItem.objects.filter(
    Q(fixed_cost_price__isnull=True) | Q(fixed_cost_price=0)
).select_related('fabric_color__fabric')

updated_count = 0
error_count = 0

for item in empty_items:
    try:
        if item.fabric_color and item.fabric_color.fabric and item.fabric_color.fabric.cost_price:
            item.fixed_cost_price = item.fabric_color.fabric.cost_price
            item.save()
            updated_count += 1
            print(f'Обновлена позиция {item.id}: {item.fabric_color.fabric.name} - {item.fixed_cost_price} ₸')
        else:
            error_count += 1
            print(f'ОШИБКА: Позиция {item.id} - нет данных о ткани или стоимости')
    except Exception as e:
        error_count += 1
        print(f'ОШИБКА при обновлении позиции {item.id}: {e}')

print(f'')
print(f'=== РЕЗУЛЬТАТ ===')
print(f'Успешно обновлено: {updated_count} позиций')
print(f'Ошибок: {error_count} позиций')
"

echo ""
echo "Проверяем результат..."
python manage.py shell -c "
from deals.models import DealItem
from django.db.models import Q

# Проверяем количество записей с пустым fixed_cost_price после обновления
empty_fixed_cost = DealItem.objects.filter(
    Q(fixed_cost_price__isnull=True) | Q(fixed_cost_price=0)
).count()

filled_fixed_cost = DealItem.objects.filter(
    fixed_cost_price__isnull=False,
    fixed_cost_price__gt=0
).count()

print(f'После обновления:')
print(f'Позиций с пустым fixed_cost_price: {empty_fixed_cost}')
print(f'Позиций с заполненным fixed_cost_price: {filled_fixed_cost}')
"

echo ""
echo "=== Заполнение завершено ==="
