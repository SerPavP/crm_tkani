# CRM Fabrics - Система управления тканями

Django-приложение для управления клиентами, сделками, тканями и складом.

**Версия:** 1.25  
**Разработчик:** SolveMint

## Возможности

- 👥 **Управление клиентами** - Полная база клиентов с историей заказов
- 🛒 **Система сделок** - Создание и управление заказами
- 🎨 **Каталог тканей** - Управление тканями, цветами и рулонами
- 📦 **Складской учет** - Штрих-коды, сканирование, отслеживание рулонов
- 💰 **Финансовая аналитика** - Топ-20 клиентов и тканей, статистика
- 📊 **Экспорт данных** - PDF и Excel отчеты
- 🔐 **Система ролей** - Админ, бухгалтер, складской работник
- 🌐 **Модальные окна** - Быстрое создание сделок с любой страницы

## Установка и запуск

### Требования
- Python 3.11+
- pip
- PostgreSQL (рекомендуется для продакшена) или SQLite (для разработки)

### Быстрый старт

#### 1. Клонирование и настройка
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

#### 2. Настройка базы данных

##### SQLite (для разработки)
```bash
# Примените миграции
python manage.py migrate

# Создайте суперпользователя
python manage.py createsuperuser
```

##### PostgreSQL (для продакшена)
1. Создайте файл `.env` из шаблона:
```bash
cp env_template.txt .env
```

2. Отредактируйте файл `.env`:
```env
DEBUG=False
SECRET_KEY=ваш_секретный_ключ
ALLOWED_HOSTS=ваш_домен.com,www.ваш_домен.com
DB_NAME=crm_tkani
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

3. Создайте базу данных в PostgreSQL:
```bash
# Войдите в PostgreSQL
sudo -u postgres psql

# Создайте базу данных
CREATE DATABASE crm_tkani;

# Создайте пользователя
CREATE USER your_username WITH PASSWORD 'your_password';

# Предоставьте права
GRANT ALL PRIVILEGES ON DATABASE crm_tkani TO your_username;

# Выйдите из PostgreSQL
\q
```

4. Примените миграции:
```bash
python manage.py migrate
python manage.py createsuperuser
```

5. Для миграции данных из SQLite в PostgreSQL:
**Способ 1: Простой скрипт (Рекомендуется)**
```bash
# Windows
migrate_to_postgres.bat

# Linux/Ubuntu
./migrate_to_postgres.sh

# Или напрямую
python migrate_to_postgres_simple.py
```

**Способ 2: Django Management команда**
```bash
python manage.py migrate_to_postgres --db-password your_password
```

**Способ 3: Оригинальный скрипт**
```bash
python migrate_to_postgres.py --db-password your_password
```

#### 3. Запуск сервера
```bash
# Разработка
python manage.py runserver

# Продакшен (Ubuntu)
gunicorn crm_fabrics.wsgi:application --bind 0.0.0.0:8000
```

#### 4. Доступ к приложению
Откройте браузер и перейдите по адресу: http://127.0.0.1:8000/

## Структура проекта

```
crm_fabrics/
├── clients/          # Управление клиентами
├── deals/            # Управление сделками и заказами
├── fabrics/          # Управление тканями и цветами
├── warehouse/        # Складской учет и штрих-коды
├── finances/         # Финансовая аналитика
├── core/             # Основные функции и утилиты
├── templates/        # HTML шаблоны
├── staticfiles/      # Статические файлы (CSS, JS)
└── media/            # Загруженные файлы
```

## Основные зависимости

- **Django 4.2.23** - Web-фреймворк
- **Django REST Framework 3.15.1** - API
- **psycopg2-binary 2.9.9** - PostgreSQL драйвер
- **reportlab 4.4.2** - Генерация PDF отчетов
- **openpyxl 3.1.5** - Работа с Excel файлами
- **python-barcode 0.15.1** - Генерация штрих-кодов
- **pyzbar 0.1.9** - Сканирование штрих-кодов
- **Pillow 10.4.0** - Обработка изображений

## Роли пользователей

### 👑 Администратор
- Полный доступ ко всем функциям
- Управление пользователями
- Просмотр финансовой аналитики
- Доступ к себестоимости товаров

### 💼 Бухгалтер
- Создание и управление сделками
- Просмотр финансовых отчетов
- Работа с клиентами
- Ограниченный доступ к ценам

### 📦 Складской работник
- Сканирование штрих-кодов
- Управление рулонами
- Просмотр тканей
- История операций

## Развертывание на Ubuntu

Подробная инструкция по развертыванию на Ubuntu сервере доступна в файле [developer_guide.md](developer_guide.md).

### Краткая инструкция:
```bash
# Установка зависимостей
sudo apt update && sudo apt install -y python3 python3-pip python3-venv nginx postgresql

# Настройка проекта
git clone <repository_url> crm_fabrics
cd crm_fabrics
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Настройка базы данных
python manage.py migrate
python manage.py collectstatic

# Запуск с Gunicorn
gunicorn crm_fabrics.wsgi:application --bind 0.0.0.0:8000
```

## Развертывание на Windows

### 1. Установка Python
- Скачайте Python 3.11+ с [python.org](https://python.org)
- Установите с опцией "Add to PATH"

### 2. Установка PostgreSQL (опционально)
- Скачайте PostgreSQL с [postgresql.org](https://postgresql.org)
- Создайте базу данных и пользователя

### 3. Настройка проекта
```cmd
# Клонирование проекта
git clone <repository_url> crm_fabrics
cd crm_fabrics

# Создание виртуального окружения
python -m venv venv
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка базы данных
python manage.py migrate
python manage.py createsuperuser

# Запуск сервера
python manage.py runserver
```

## Возможные проблемы

### Ошибка "No module named 'rest_framework'"
```bash
pip install -r requirements.txt
```

### Ошибка политики выполнения PowerShell (Windows)
```bash
.\venv\Scripts\python.exe manage.py runserver
```

### Проблемы с PostgreSQL
1. **Ошибка подключения**:
   - Проверьте, что сервис PostgreSQL запущен
   - Убедитесь, что настройки в `.env` корректны
   - Проверьте доступность: `pg_isready -h localhost -p 5432`

2. **Ошибка "psycopg2 не найден"**:
   ```bash
   pip install psycopg2-binary
   ```

### Проблемы с виртуальным окружением
```bash
# Создание нового окружения
python -m venv venv_new
venv_new\Scripts\python.exe -m pip install -r requirements.txt
```

## История версий

- **v1.25** - Модальные окна, кликабельные элементы, улучшения PDF
- **v1.2.5** - Переход на PostgreSQL, безопасность
- **v1.2.1** - Исправления цен и себестоимости
- **v1.2** - Удаление диаграмм, история удаления рулонов
- **v1.1.5** - Диаграммы в финансах, топ-20 рейтинги
- **v1.1** - История клиентов и складских операций
- **v1.00** - Официальный запуск, финансы, скрытие цен

Полная история версий доступна в [CHANGELOG.md](CHANGELOG.md).

## Поддержка

Для получения поддержки или сообщения об ошибках создайте issue в репозитории проекта.

---

**Создано SolveMint | Версия 1.25**