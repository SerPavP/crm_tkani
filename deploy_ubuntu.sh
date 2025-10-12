#!/bin/bash

# ========================================
# CRM Fabrics - Скрипт развертывания на Ubuntu
# ========================================

set -e  # Остановка при ошибке
set -u  # Ошибка при использовании неопределенных переменных
set -o pipefail  # Ошибка в любой части pipeline

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода с цветом
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Обработчик ошибок
error_exit() {
    local line_no=$1
    local bash_lineno=$2
    local last_command=$3
    local exit_code=$4
    
    echo ""
    print_error "================================================"
    print_error "КРИТИЧЕСКАЯ ОШИБКА!"
    print_error "================================================"
    print_error "Скрипт остановлен из-за ошибки!"
    echo ""
    print_error "Детали ошибки:"
    echo "  - Строка: $line_no"
    echo "  - Команда: $last_command"
    echo "  - Код ошибки: $exit_code"
    echo ""
    print_error "Развертывание прервано. Исправьте ошибку и запустите скрипт заново."
    echo ""
    exit $exit_code
}

# Установка ловушки для перехвата ошибок
trap 'error_exit ${LINENO} ${BASH_LINENO} "$BASH_COMMAND" $?' ERR

print_header() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
    echo ""
}

# Проверка, что скрипт запущен из корня проекта
if [ ! -f "manage.py" ]; then
    print_error "Файл manage.py не найден!"
    print_error "Убедитесь, что вы запускаете скрипт из корневой папки проекта."
    exit 1
fi

print_header "CRM Fabrics - Развертывание на Ubuntu"

# ========================================
# 1. Обновление системы
# ========================================
print_header "Шаг 1: Обновление системы"
print_info "Обновление списка пакетов..."
sudo apt update

print_info "Обновление установленных пакетов..."
sudo apt upgrade -y

print_success "Система обновлена"

# ========================================
# 2. Установка необходимых пакетов
# ========================================
print_header "Шаг 2: Установка необходимых пакетов"

print_info "Установка Python и зависимостей..."
sudo apt install -y python3 python3-pip python3-venv python3-dev

print_info "Установка PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib libpq-dev

print_info "Установка дополнительных пакетов..."
sudo apt install -y build-essential libssl-dev libffi-dev libzbar0 libzbar-dev

print_info "Установка Nginx и других утилит..."
sudo apt install -y nginx git curl

print_success "Все пакеты установлены"

# ========================================
# 3. Настройка PostgreSQL
# ========================================
print_header "Шаг 3: Настройка PostgreSQL"

print_info "Запуск PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

print_success "PostgreSQL запущен"

# Запрос параметров базы данных
echo ""
print_info "Введите параметры для базы данных PostgreSQL:"
echo ""

read -p "Имя базы данных [crm_tkani]: " DB_NAME
DB_NAME=${DB_NAME:-crm_tkani}

read -p "Имя пользователя БД [crm_user]: " DB_USER
DB_USER=${DB_USER:-crm_user}

read -sp "Пароль для БД (по умолчанию: 12345): " DB_PASSWORD
echo ""
if [ -z "$DB_PASSWORD" ]; then
    DB_PASSWORD="12345"
    print_warning "Используется пароль по умолчанию: 12345"
fi

read -p "Хост БД [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "Порт БД [5432]: " DB_PORT
DB_PORT=${DB_PORT:-5432}

echo ""
print_info "Создание базы данных и пользователя..."

# Создание пользователя и базы данных
sudo -u postgres psql <<EOF
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\q
EOF

print_success "База данных создана"

# ========================================
# 4. Настройка Python окружения
# ========================================
print_header "Шаг 4: Настройка Python окружения"

print_info "Создание виртуального окружения..."
python3 -m venv venv

print_info "Активация виртуального окружения..."
source venv/bin/activate

print_info "Обновление pip..."
pip install --upgrade pip

print_info "Установка зависимостей из requirements.txt..."
pip install -r requirements.txt

print_info "Установка Gunicorn для продакшена..."
pip install gunicorn

print_success "Python окружение настроено"

# ========================================
# 5. Создание файла .env
# ========================================
print_header "Шаг 5: Настройка переменных окружения"

# Генерация SECRET_KEY
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

# Запрос домена
echo ""
read -p "Введите домен сайта (например, crm-tkani.kz): " DOMAIN
read -p "Введите IP адрес сервера: " SERVER_IP

print_info "Создание файла .env..."

cat > .env <<EOF
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,$SERVER_IP,localhost,127.0.0.1

# PostgreSQL Database Configuration
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT

# CSRF settings
CSRF_TRUSTED_ORIGINS=https://$DOMAIN,https://www.$DOMAIN,http://$SERVER_IP
EOF

print_success "Файл .env создан"

# ========================================
# 6. Применение миграций
# ========================================
print_header "Шаг 6: Применение миграций Django"

print_info "Применение миграций к базе данных..."
python manage.py migrate

print_success "Миграции применены"

# ========================================
# 7. Импорт данных из SQLite (если есть дамп)
# ========================================
print_header "Шаг 7: Импорт данных"

if [ -f "dan/db.sqlite3" ]; then
    print_info "Обнаружена база данных SQLite в папке dan/"
    read -p "Импортировать данные из SQLite? (y/N): " IMPORT_DATA
    
    if [[ $IMPORT_DATA =~ ^[Yy]$ ]]; then
        print_info "Экспорт данных из SQLite..."
        
        # Временно переключаемся на SQLite для экспорта
        python export_data.py
        
        if [ -f "db_dump.json" ]; then
            print_info "Импорт данных в PostgreSQL..."
            python manage.py loaddata db_dump.json
            
            print_info "Сброс последовательностей ID..."
            python manage.py shell <<PYEOF
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name NOT LIKE 'django_%'")
tables = cursor.fetchall()
for table in tables:
    try:
        cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table[0]}', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM {table[0]}")
    except:
        pass
print("Sequences reset successfully")
PYEOF
            
            print_success "Данные импортированы"
        else
            print_error "Файл db_dump.json не найден"
        fi
    fi
else
    print_warning "База данных SQLite не найдена. Пропускаем импорт данных."
fi

# ========================================
# 8. Создание суперпользователя
# ========================================
print_header "Шаг 8: Создание суперпользователя"

print_info "Создание администратора Django..."
python manage.py createsuperuser

print_success "Суперпользователь создан"

# ========================================
# 9. Сбор статических файлов
# ========================================
print_header "Шаг 9: Сбор статических файлов"

print_info "Сбор статических файлов..."
python manage.py collectstatic --noinput

print_success "Статические файлы собраны"

# ========================================
# 10. Настройка Gunicorn
# ========================================
print_header "Шаг 10: Настройка Gunicorn"

print_info "Создание конфигурации Gunicorn..."

cat > gunicorn.conf.py <<'EOF'
# Gunicorn конфигурация для CRM Fabrics
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = True
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
EOF

# Создание директории для логов
mkdir -p logs
mkdir -p media

print_success "Конфигурация Gunicorn создана"

# ========================================
# 11. Настройка systemd сервиса
# ========================================
print_header "Шаг 11: Настройка systemd сервиса"

CURRENT_USER=$(whoami)
CURRENT_DIR=$(pwd)

print_info "Создание systemd сервиса..."

sudo tee /etc/systemd/system/crmfabrics.service > /dev/null <<EOF
[Unit]
Description=CRM Fabrics Django Application
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
Environment="PATH=$CURRENT_DIR/venv/bin"
ExecStart=$CURRENT_DIR/venv/bin/gunicorn --config gunicorn.conf.py crm_fabrics.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

print_success "Systemd сервис создан"

# ========================================
# 12. Настройка Nginx
# ========================================
print_header "Шаг 12: Настройка Nginx"

print_info "Создание конфигурации Nginx..."

sudo tee /etc/nginx/sites-available/crmfabrics > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN $SERVER_IP;

    # Размер загружаемых файлов
    client_max_body_size 50M;

    # Статические файлы
    location /static/ {
        alias $CURRENT_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Медиа файлы
    location /media/ {
        alias $CURRENT_DIR/media/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # Основное приложение
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        proxy_buffering off;
    }
}
EOF

# Активация сайта
print_info "Активация сайта..."
sudo ln -sf /etc/nginx/sites-available/crmfabrics /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Проверка конфигурации Nginx
print_info "Проверка конфигурации Nginx..."
sudo nginx -t

print_success "Nginx настроен"

# ========================================
# 13. Настройка файрвола
# ========================================
print_header "Шаг 13: Настройка файрвола"

print_info "Настройка UFW..."
sudo apt install -y ufw
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

print_success "Файрвол настроен"

# ========================================
# 14. Запуск сервисов
# ========================================
print_header "Шаг 14: Запуск сервисов"

print_info "Перезагрузка конфигурации systemd..."
sudo systemctl daemon-reload

print_info "Запуск и включение CRM Fabrics..."
sudo systemctl enable crmfabrics
sudo systemctl start crmfabrics

print_info "Перезапуск Nginx..."
sudo systemctl restart nginx

# Проверка статуса
sleep 2
if sudo systemctl is-active --quiet crmfabrics; then
    print_success "CRM Fabrics запущен"
else
    print_error "Ошибка запуска CRM Fabrics"
    print_info "Проверьте логи: sudo journalctl -u crmfabrics -n 50"
fi

if sudo systemctl is-active --quiet nginx; then
    print_success "Nginx запущен"
else
    print_error "Ошибка запуска Nginx"
fi

# ========================================
# Финальная информация
# ========================================
print_header "✅ Развертывание завершено!"

echo ""
print_success "CRM Fabrics успешно развернут на Ubuntu!"
echo ""
print_info "Информация о развертывании:"
echo "  - Домен: http://$DOMAIN"
echo "  - IP: http://$SERVER_IP"
echo "  - База данных: $DB_NAME"
echo "  - Пользователь БД: $DB_USER"
echo ""
print_info "Команды для управления:"
echo "  - Статус: sudo systemctl status crmfabrics"
echo "  - Остановить: sudo systemctl stop crmfabrics"
echo "  - Запустить: sudo systemctl start crmfabrics"
echo "  - Перезапустить: sudo systemctl restart crmfabrics"
echo "  - Логи: sudo journalctl -u crmfabrics -f"
echo ""
print_info "Следующие шаги:"
echo "  1. Настройте SSL сертификат: sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo "  2. Проверьте работу сайта: http://$DOMAIN"
echo "  3. Войдите в админку: http://$DOMAIN/admin/"
echo ""
print_warning "Важно:"
echo "  - Файл .env содержит пароли - храните его в безопасности!"
echo "  - Мониторьте логи на предмет ошибок"
echo "  - Настройте снапшоты диска в Google Cloud Console для резервного копирования"
echo ""
print_success "Готово! 🎉"

