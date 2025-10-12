#!/bin/bash

echo "========================================"
echo "CRM Fabrics - Миграция в PostgreSQL"
echo "========================================"
echo

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Ошибка: Python3 не найден"
    echo "   Установите Python 3.11+"
    exit 1
fi

# Проверяем наличие manage.py
if [ ! -f "manage.py" ]; then
    echo "❌ Ошибка: Файл manage.py не найден"
    echo "   Убедитесь, что вы запускаете скрипт из корневой папки проекта"
    exit 1
fi

# Активируем виртуальное окружение если оно существует
if [ -f "venv/bin/activate" ]; then
    echo "🔧 Активация виртуального окружения..."
    source venv/bin/activate
fi

# Запускаем скрипт миграции
echo "🚀 Запуск миграции..."
python3 migrate_to_postgres_simple.py

echo
echo "========================================"
echo "Миграция завершена"
echo "========================================"
