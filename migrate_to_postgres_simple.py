#!/usr/bin/env python
"""
Простой скрипт для миграции данных из SQLite в PostgreSQL.
Использует Django management команду для безопасной миграции.
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Основная функция для запуска миграции."""
    print("🚀 CRM Fabrics - Миграция из SQLite в PostgreSQL")
    print("=" * 50)
    
    # Проверяем, что мы в корневой папке проекта
    if not Path('manage.py').exists():
        print("❌ Ошибка: Файл manage.py не найден.")
        print("   Убедитесь, что вы запускаете скрипт из корневой папки проекта.")
        return 1
    
    # Получаем параметры от пользователя
    print("\n📋 Введите параметры подключения к PostgreSQL:")
    
    db_name = input("Имя базы данных [crm_tkani]: ").strip() or "crm_tkani"
    db_user = input("Пользователь [postgres]: ").strip() or "postgres"
    db_password = input("Пароль: ").strip()
    
    if not db_password:
        print("❌ Ошибка: Пароль не может быть пустым.")
        return 1
    
    db_host = input("Хост [localhost]: ").strip() or "localhost"
    db_port = input("Порт [5432]: ").strip() or "5432"
    
    print(f"\n🔧 Параметры подключения:")
    print(f"   База данных: {db_name}")
    print(f"   Пользователь: {db_user}")
    print(f"   Хост: {db_host}")
    print(f"   Порт: {db_port}")
    
    confirm = input("\n❓ Продолжить миграцию? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes', 'да', 'д']:
        print("❌ Миграция отменена.")
        return 0
    
    # Формируем команду
    cmd = [
        'python', 'manage.py', 'migrate_to_postgres',
        '--db-name', db_name,
        '--db-user', db_user,
        '--db-password', db_password,
        '--db-host', db_host,
        '--db-port', db_port
    ]
    
    print(f"\n🔄 Запуск команды: {' '.join(cmd[:6])} [пароль скрыт]")
    print("=" * 50)
    
    try:
        # Запускаем команду
        result = subprocess.run(cmd, check=True)
        
        print("\n" + "=" * 50)
        print("✅ Миграция завершена успешно!")
        print("\n📝 Следующие шаги:")
        print("1. Проверьте файл .env - он должен содержать настройки PostgreSQL")
        print("2. Перезапустите сервер: python manage.py runserver")
        print("3. Проверьте работу приложения")
        print("4. Создайте резервную копию старой SQLite базы")
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка при выполнении миграции: {e}")
        print("\n🔧 Возможные решения:")
        print("1. Проверьте, что PostgreSQL запущен")
        print("2. Убедитесь, что пользователь имеет права на создание баз данных")
        print("3. Проверьте правильность пароля")
        print("4. Убедитесь, что порт 5432 доступен")
        return 1
        
    except KeyboardInterrupt:
        print("\n❌ Миграция прервана пользователем.")
        return 1
        
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
