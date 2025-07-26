# Инструкция по развертыванию CRM Fabrics на Ubuntu VM

## Анализ готовности проекта

### ✅ Что готово к продакшену:
- Все зависимости указаны в `requirements.txt`
- Настроены статические файлы (`STATIC_ROOT`, `STATIC_URL`)
- Настроены медиа файлы (`MEDIA_ROOT`, `MEDIA_URL`)
- Настроены CSRF trusted origins
- Используется SQLite (простая миграция)

### ⚠️ Что нужно исправить перед продакшеном:
- `DEBUG = True` - нужно изменить на `False`
- `SECRET_KEY` в коде - нужно вынести в переменные окружения
- `ALLOWED_HOSTS = ['*']` - нужно указать конкретные домены

## Пошаговая инструкция развертывания

### 1. Подготовка Ubuntu VM

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y python3 python3-pip python3-venv nginx git curl

# Установка дополнительных зависимостей для работы с изображениями
sudo apt install -y libpq-dev python3-dev build-essential libssl-dev libffi-dev

# Установка системных библиотек для работы с штрих-кодами
sudo apt install -y libzbar0 libzbar-dev

# Установка PostgreSQL (рекомендуется для продакшена)
sudo apt install -y postgresql postgresql-contrib
```

### 2. Создание пользователя для приложения

```bash
# Создание пользователя
sudo adduser crmfabrics
sudo usermod -aG sudo crmfabrics

# Переключение на пользователя
sudo su - crmfabrics
```

### 3. Клонирование проекта

```bash
# Переход в домашнюю директорию
cd ~

# Клонирование проекта (замените на ваш репозиторий)
git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ> crm_fabrics
cd crm_fabrics

# Или если у вас нет Git репозитория, загрузите файлы через SCP/SFTP
```

### 4. Настройка Python окружения

```bash
# Создание виртуального окружения
python3 -m venv venv

# Активация виртуального окружения
source venv/bin/activate

# Обновление pip
pip install --upgrade pip

# Установка зависимостей
pip install -r requirements.txt

# Установка дополнительных пакетов для продакшена
pip install gunicorn psycopg2-binary
```

### 5. Настройка переменных окружения

```bash
# Создание файла с переменными окружения
nano .env
```

Содержимое файла `.env`:
```env
DEBUG=False
SECRET_KEY=ваш_новый_секретный_ключ_здесь
ALLOWED_HOSTS=ваш_домен.com,www.ваш_домен.com,IP_АДРЕС_СЕРВЕРА
DATABASE_URL=sqlite:///db.sqlite3
```

### 6. Настройка Django для продакшена

Создайте файл `crm_fabrics/settings_production.py`:

```python
from .settings import *
import os
from pathlib import Path

# Безопасность
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-for-production')

# Разрешенные хосты
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Статические файлы
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

# Медиа файлы
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# Логирование
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# HTTPS настройки
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
```

### 7. Создание директорий и настройка прав

```bash
# Создание директории для логов
mkdir logs
mkdir media

# Настройка прав доступа
chmod 755 logs media
chmod 644 .env
```

### 8. Применение миграций и создание суперпользователя

```bash
# Применение миграций
python manage.py migrate --settings=crm_fabrics.settings_production

# Создание суперпользователя
python manage.py createsuperuser --settings=crm_fabrics.settings_production

# Сбор статических файлов
python manage.py collectstatic --settings=crm_fabrics.settings_production --noinput
```

### 9. Настройка Gunicorn

Создайте файл `gunicorn.conf.py`:

```python
# Gunicorn конфигурация
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = True
```

### 10. Настройка systemd сервиса

Создайте файл `/etc/systemd/system/crmfabrics.service`:

```ini
[Unit]
Description=CRM Fabrics Django Application
After=network.target

[Service]
Type=notify
User=crmfabrics
Group=crmfabrics
WorkingDirectory=/home/crmfabrics/crm_fabrics
Environment=PATH=/home/crmfabrics/crm_fabrics/venv/bin
ExecStart=/home/crmfabrics/crm_fabrics/venv/bin/gunicorn --config gunicorn.conf.py crm_fabrics.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### 11. Настройка Nginx

Создайте файл `/etc/nginx/sites-available/crmfabrics`:

```nginx
server {
    listen 80;
    server_name ваш_домен.com www.ваш_домен.com;

    # Редирект на HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ваш_домен.com www.ваш_домен.com;

    # SSL сертификаты (замените на ваши)
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;

    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Размер загружаемых файлов
    client_max_body_size 10M;

    # Статические файлы
    location /static/ {
        alias /home/crmfabrics/crm_fabrics/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Медиа файлы
    location /media/ {
        alias /home/crmfabrics/crm_fabrics/media/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # Основное приложение
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

### 12. Активация сервисов

```bash
# Активация Nginx сайта
sudo ln -s /etc/nginx/sites-available/crmfabrics /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Удаление дефолтного сайта

# Проверка конфигурации Nginx
sudo nginx -t

# Перезапуск Nginx
sudo systemctl restart nginx

# Включение и запуск Django сервиса
sudo systemctl enable crmfabrics
sudo systemctl start crmfabrics

# Проверка статуса
sudo systemctl status crmfabrics
```

### 13. Настройка файрвола

```bash
# Установка UFW
sudo apt install ufw

# Настройка правил
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 14. Настройка SSL сертификатов (Let's Encrypt)

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx

# Получение SSL сертификата
sudo certbot --nginx -d ваш_домен.com -d www.ваш_домен.com

# Автоматическое обновление сертификатов
sudo crontab -e
# Добавьте строку:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### 15. Мониторинг и логи

```bash
# Просмотр логов Django
tail -f /home/crmfabrics/crm_fabrics/logs/django.log

# Просмотр логов Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Просмотр логов systemd
sudo journalctl -u crmfabrics -f
```

### 16. Резервное копирование

Создайте скрипт `/home/crmfabrics/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/home/crmfabrics/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Создание директории для бэкапов
mkdir -p $BACKUP_DIR

# Бэкап базы данных
cp /home/crmfabrics/crm_fabrics/db.sqlite3 $BACKUP_DIR/db_$DATE.sqlite3

# Бэкап медиа файлов
tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C /home/crmfabrics/crm_fabrics media/

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "*.sqlite3" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

```bash
# Сделать скрипт исполняемым
chmod +x /home/crmfabrics/backup.sh

# Добавить в cron для ежедневного бэкапа
crontab -e
# Добавьте строку:
# 0 2 * * * /home/crmfabrics/backup.sh
```

## Команды для быстрой проверки

```bash
# Проверка статуса сервисов
sudo systemctl status nginx
sudo systemctl status crmfabrics

# Проверка портов
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
sudo netstat -tlnp | grep :8000

# Проверка прав доступа
ls -la /home/crmfabrics/crm_fabrics/
ls -la /home/crmfabrics/crm_fabrics/media/
ls -la /home/crmfabrics/crm_fabrics/logs/
```

## Устранение неполадок

### Если приложение не запускается:
```bash
# Проверка логов
sudo journalctl -u crmfabrics -n 50

# Проверка прав доступа
sudo chown -R crmfabrics:crmfabrics /home/crmfabrics/crm_fabrics/
```

### Если статические файлы не загружаются:
```bash
# Пересборка статических файлов
cd /home/crmfabrics/crm_fabrics/
source venv/bin/activate
python manage.py collectstatic --settings=crm_fabrics.settings_production --noinput
```

### Если база данных заблокирована:
```bash
# Проверка процессов SQLite
sudo fuser /home/crmfabrics/crm_fabrics/db.sqlite3
```

## Рекомендации по безопасности

1. **Регулярно обновляйте систему:**
   ```bash
   sudo apt update && sudo apt upgrade
   ```

2. **Используйте сильные пароли для всех пользователей**

3. **Настройте регулярные бэкапы**

4. **Мониторьте логи на предмет подозрительной активности**

5. **Используйте HTTPS для всех соединений**

6. **Ограничьте доступ к серверу только необходимыми портами**

## Переход на PostgreSQL (опционально)

Если вы хотите использовать PostgreSQL вместо SQLite:

```bash
# Создание базы данных
sudo -u postgres createdb crmfabrics
sudo -u postgres createuser crmfabrics_user

# Настройка прав доступа
sudo -u postgres psql
GRANT ALL PRIVILEGES ON DATABASE crmfabrics TO crmfabrics_user;
\q

# Обновление settings_production.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'crmfabrics',
        'USER': 'crmfabrics_user',
        'PASSWORD': 'ваш_пароль',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## Заключение

После выполнения всех шагов ваше приложение будет доступно по адресу `https://ваш_домен.com` и будет готово к продакшену.

Не забудьте:
- Заменить `ваш_домен.com` на реальный домен
- Настроить SSL сертификаты
- Создать сильный SECRET_KEY
- Настроить регулярные бэкапы
- Мониторить логи и производительность