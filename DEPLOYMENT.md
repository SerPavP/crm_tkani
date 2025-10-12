# 🚀 Инструкция по развертыванию CRM Fabrics на Ubuntu

## Быстрый старт

### 1. Подготовка на локальной машине

```bash
# Убедитесь, что все изменения закоммичены
git add .
git commit -m "Ready for production deployment"
git push origin prod
```

### 2. Подключение к Ubuntu серверу

```bash
# Подключитесь к серверу через SSH
ssh your_user@your_server_ip
```

### 3. Клонирование проекта

```bash
# Клонируйте проект из ветки prod
git clone -b prod --single-branch https://github.com/SerPavP/crm_tkani.git
cd crm_tkani
```

### 4. Запуск скрипта развертывания

```bash
# Сделайте скрипт исполняемым
chmod +x deploy_ubuntu.sh

# Запустите скрипт
./deploy_ubuntu.sh
```

## Что делает скрипт?

Скрипт автоматически выполнит следующие действия:

1. ✅ **Обновление системы** - обновит Ubuntu до последней версии
2. ✅ **Установка пакетов** - установит Python, PostgreSQL, Nginx и другие зависимости
3. ✅ **Настройка PostgreSQL** - создаст базу данных и пользователя
4. ✅ **Python окружение** - создаст виртуальное окружение и установит зависимости
5. ✅ **Файл .env** - создаст конфигурацию с переменными окружения
6. ✅ **Миграции Django** - применит все миграции к базе данных
7. ✅ **Импорт данных** - импортирует данные из SQLite (если есть)
8. ✅ **Суперпользователь** - создаст администратора системы
9. ✅ **Статические файлы** - соберет все статические файлы
10. ✅ **Gunicorn** - настроит WSGI сервер
11. ✅ **Systemd** - создаст системный сервис для автозапуска
12. ✅ **Nginx** - настроит веб-сервер
13. ✅ **Файрвол** - настроит UFW для безопасности
14. ✅ **Запуск сервисов** - запустит приложение

## Параметры, которые нужно будет ввести

Во время выполнения скрипта вам будет предложено ввести:

### Параметры базы данных:
- **Имя базы данных** (по умолчанию: `crm_tkani`)
- **Имя пользователя БД** (по умолчанию: `crm_user`)
- **Пароль для БД** (по умолчанию: `12345` - рекомендуется изменить!)
- **Хост БД** (по умолчанию: `localhost`)
- **Порт БД** (по умолчанию: `5432`)

### Параметры домена:
- **Домен сайта** (например: `crm-tkani.kz`)
- **IP адрес сервера** (внешний IP вашего сервера)

### Создание суперпользователя:
- **Имя пользователя**
- **Email**
- **Пароль**

### Импорт данных:
- **Импортировать данные из SQLite?** (y/N)

## После развертывания

### Проверка работы

```bash
# Проверка статуса сервиса
sudo systemctl status crmfabrics

# Проверка логов
sudo journalctl -u crmfabrics -f

# Проверка Nginx
sudo systemctl status nginx
```

### Настройка SSL (Let's Encrypt)

```bash
# Установка Certbot
sudo apt install -y certbot python3-certbot-nginx

# Получение SSL сертификата
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Автоматическое обновление сертификатов
sudo crontab -e
# Добавьте: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Доступ к приложению

- **Веб-интерфейс**: `http://your-domain.com`
- **Админка**: `http://your-domain.com/admin/`

## Команды управления

### Управление сервисом

```bash
# Запуск
sudo systemctl start crmfabrics

# Остановка
sudo systemctl stop crmfabrics

# Перезапуск
sudo systemctl restart crmfabrics

# Статус
sudo systemctl status crmfabrics

# Просмотр логов
sudo journalctl -u crmfabrics -f
```

### Обновление приложения

```bash
# Перейдите в папку проекта
cd ~/crm_tkani

# Получите последние изменения
git pull origin prod

# Активируйте виртуальное окружение
source venv/bin/activate

# Установите новые зависимости (если есть)
pip install -r requirements.txt

# Применить миграции
python manage.py migrate

# Собрать статику
python manage.py collectstatic --noinput

# Перезапустить сервис
sudo systemctl restart crmfabrics
```

### Резервное копирование

⚠️ **Важно:** Используйте встроенные механизмы резервного копирования Google Cloud:

```bash
# В Google Cloud Console настройте:
# 1. Снапшоты дисков (Snapshots)
# 2. Автоматическое расписание снапшотов
# 3. Политику хранения (рекомендуется 7-30 дней)
```

Для ручного бэкапа базы данных:
```bash
# Создать дамп базы данных
PGPASSWORD="your_password" pg_dump -h localhost -U crm_user crm_tkani > backup_$(date +%Y%m%d).sql

# Восстановить из дампа
PGPASSWORD="your_password" psql -h localhost -U crm_user crm_tkani < backup_20250112.sql
```

## Структура проекта после развертывания

```
crm_tkani/
├── venv/                    # Виртуальное окружение Python
├── staticfiles/             # Собранные статические файлы
├── media/                   # Загруженные медиа файлы
├── logs/                    # Логи приложения
│   ├── gunicorn_access.log
│   └── gunicorn_error.log
├── .env                     # Конфигурация (НЕ коммитить!)
├── gunicorn.conf.py         # Конфигурация Gunicorn
├── deploy_ubuntu.sh         # Скрипт развертывания
└── manage.py                # Django manage
```

## Устранение неполадок

### Приложение не запускается

```bash
# Проверьте логи
sudo journalctl -u crmfabrics -n 100 --no-pager

# Проверьте права доступа
ls -la /path/to/crm_tkani/

# Попробуйте запустить вручную
cd /path/to/crm_tkani/
source venv/bin/activate
gunicorn --config gunicorn.conf.py crm_fabrics.wsgi:application
```

### База данных недоступна

```bash
# Проверьте статус PostgreSQL
sudo systemctl status postgresql

# Проверьте подключение
psql -h localhost -U crm_user -d crm_tkani

# Проверьте настройки в .env
cat .env | grep DB_
```

### Статические файлы не загружаются

```bash
# Пересоберите статику
cd /path/to/crm_tkani/
source venv/bin/activate
python manage.py collectstatic --noinput

# Проверьте права доступа
chmod -R 755 staticfiles/
```

### Nginx показывает ошибку 502

```bash
# Проверьте, что Gunicorn запущен
sudo systemctl status crmfabrics

# Проверьте логи Nginx
sudo tail -f /var/log/nginx/error.log

# Проверьте, что Gunicorn слушает на правильном порту
sudo netstat -tlnp | grep 8000
```

## Безопасность

### Обязательные меры безопасности:

1. ✅ Используйте сильные пароли для всех пользователей
2. ✅ Настройте SSL сертификаты (Let's Encrypt)
3. ✅ Регулярно обновляйте систему: `sudo apt update && sudo apt upgrade`
4. ✅ Мониторьте логи на предмет подозрительной активности
5. ✅ Делайте регулярные резервные копии
6. ✅ Ограничьте доступ к серверу через SSH (используйте ключи)
7. ✅ Настройте fail2ban для защиты от брутфорса

### Дополнительные рекомендации:

- Не храните пароли в коде
- Не коммитьте файл `.env` в Git
- Используйте отдельного пользователя для PostgreSQL
- Настройте мониторинг (Prometheus, Grafana)
- Настройте алерты для критических ошибок

## Контакты и поддержка

При возникновении проблем:
1. Проверьте логи: `sudo journalctl -u crmfabrics -f`
2. Проверьте документацию: `developer_guide.md`
3. Проверьте настройки: `cat .env`

## Чеклист перед продакшеном

- [ ] Все изменения закоммичены в Git
- [ ] Создана свежая резервная копия данных
- [ ] Обновлены все зависимости в `requirements.txt`
- [ ] Протестирована работа приложения локально
- [ ] Настроен домен и DNS записи
- [ ] Сервер Ubuntu создан и доступен по SSH
- [ ] Выполнен скрипт `deploy_ubuntu.sh`
- [ ] Настроены SSL сертификаты
- [ ] Проверена работа всех функций
- [ ] Настроено автоматическое резервное копирование
- [ ] Настроен мониторинг

---

**Успешного развертывания! 🚀**

