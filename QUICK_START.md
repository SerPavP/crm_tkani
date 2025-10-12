# 🚀 Быстрый старт - CRM Fabrics на Ubuntu

## Шаги развертывания

### 1️⃣ На локальной машине

```bash
# Коммит и пуш в prod ветку
git add .
git commit -m "Production ready"
git push origin prod
```

### 2️⃣ На Ubuntu сервере

```bash
# Подключение к серверу
ssh your_user@server_ip

# Клонирование проекта
git clone -b prod --single-branch https://github.com/SerPavP/crm_tkani.git
cd crm_tkani

# Запуск развертывания
chmod +x deploy_ubuntu.sh
./deploy_ubuntu.sh
```

### 3️⃣ Во время выполнения скрипта

Вам будет предложено ввести:

**Параметры БД:**
- Имя базы: `crm_tkani` (Enter для значения по умолчанию)
- Пользователь: `crm_user` (Enter для значения по умолчанию)
- Пароль: Enter для `12345` (по умолчанию) или введите свой ⚠️
- Хост: `localhost` (Enter)
- Порт: `5432` (Enter)

**Параметры домена:**
- Домен: `crm-tkani.kz`
- IP сервера: `34.51.199.26`

**Администратор Django:**
- Username: `admin`
- Email: `admin@example.com`
- Password: `ваш_admin_пароль`

**Импорт данных:**
- Импортировать из SQLite? `y` (если есть данные в `dan/db.sqlite3`)

### 4️⃣ После завершения

```bash
# Настроить SSL
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d crm-tkani.kz -d www.crm-tkani.kz

# Проверить работу
curl http://your-domain.com
```

## ⚡ Основные команды

```bash
# Управление сервисом
sudo systemctl start crmfabrics      # Запустить
sudo systemctl stop crmfabrics       # Остановить
sudo systemctl restart crmfabrics    # Перезапустить
sudo systemctl status crmfabrics     # Статус

# Просмотр логов
sudo journalctl -u crmfabrics -f     # В реальном времени
sudo journalctl -u crmfabrics -n 100 # Последние 100 строк
```

## 💾 Резервное копирование

```bash
# Настройте снапшоты в Google Cloud Console
# Compute Engine -> Snapshots -> Create Snapshot Schedule

# Ручной бэкап базы данных
PGPASSWORD="your_password" pg_dump -h localhost -U crm_user crm_tkani > backup_$(date +%Y%m%d).sql
```

## 📦 Обновление проекта

```bash
cd ~/crm_tkani
git pull origin prod
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart crmfabrics
```

## 🆘 Если что-то пошло не так

```bash
# Проверить логи
sudo journalctl -u crmfabrics -n 50 --no-pager

# Проверить базу данных
psql -h localhost -U crm_user -d crm_tkani

# Перезапустить всё
sudo systemctl restart crmfabrics
sudo systemctl restart nginx
sudo systemctl restart postgresql

# Проверить порты
sudo netstat -tlnp | grep -E '(80|443|8000|5432)'
```

## ✅ Проверка успешного развертывания

- [ ] Сервис запущен: `sudo systemctl is-active crmfabrics` → `active`
- [ ] Nginx работает: `sudo systemctl is-active nginx` → `active`
- [ ] Сайт доступен: `curl http://your-domain.com` → 200 OK
- [ ] Админка работает: открыть `http://your-domain.com/admin/`
- [ ] Статика загружается: проверить стили на сайте
- [ ] SSL настроен: `https://your-domain.com` работает

## 📁 Важные файлы

```
~/crm_tkani/
├── .env                      # ⚠️ Конфигурация (НЕ коммитить!)
├── logs/
│   ├── gunicorn_access.log   # Логи доступа
│   └── gunicorn_error.log    # Логи ошибок
├── deploy_ubuntu.sh          # Скрипт развертывания
└── gunicorn.conf.py          # Конфигурация Gunicorn
```

---

**Время развертывания:** ~10-15 минут  
**Требования:** Ubuntu 20.04+, 2GB RAM, 20GB диск

