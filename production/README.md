# CRM Fabrics - Система управления тканями

Django-приложение для управления клиентами, сделками, тканями и складом.

## Установка и запуск

### 1. Требования
- Python 3.11+
- pip

### 2. Клонирование и настройка
```bash
# Перейдите в папку проекта
cd crm_fabrics

# Создайте виртуальное окружение
python -m venv venv

# Активируйте виртуальное окружение
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

### 3. Настройка базы данных
```bash
# Примените миграции
python manage.py migrate

# Создайте суперпользователя (опционально)
python manage.py createsuperuser
```

### 4. Запуск сервера
```bash
# Способ 1: Через командную строку
python manage.py runserver

# Способ 2: Через batch файл (Windows)
run_server.bat
```

### 5. Доступ к приложению
Откройте браузер и перейдите по адресу: http://127.0.0.1:8000/

## Структура проекта

- `clients/` - Управление клиентами
- `deals/` - Управление сделками
- `fabrics/` - Управление тканями и цветами
- `warehouse/` - Управление складом
- `finances/` - Финансовый модуль
- `core/` - Основные функции и утилиты

## Зависимости

- Django 5.0.4
- Django REST Framework 3.15.1
- ReportLab 4.0.7 (для генерации PDF)
- OpenPyXL 3.1.2 (для работы с Excel)

## Возможные проблемы

### Ошибка "No module named 'rest_framework'"
Убедитесь, что все зависимости установлены:
```bash
pip install -r requirements.txt
```

### Ошибка политики выполнения PowerShell
Если возникает ошибка с политикой выполнения, используйте:
```bash
.\venv_new\Scripts\python.exe manage.py runserver
```

### Проблемы с виртуальным окружением
Если виртуальное окружение повреждено, создайте новое:
```bash
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
``` 