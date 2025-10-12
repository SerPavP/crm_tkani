@echo off
echo ========================================
echo CRM Fabrics - Миграция в PostgreSQL
echo ========================================
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Ошибка: Python не найден в PATH
    echo    Установите Python 3.11+ и добавьте его в PATH
    pause
    exit /b 1
)

REM Проверяем наличие manage.py
if not exist "manage.py" (
    echo ❌ Ошибка: Файл manage.py не найден
    echo    Убедитесь, что вы запускаете скрипт из корневой папки проекта
    pause
    exit /b 1
)

REM Активируем виртуальное окружение если оно существует
if exist "venv\Scripts\activate.bat" (
    echo 🔧 Активация виртуального окружения...
    call venv\Scripts\activate.bat
)

REM Запускаем скрипт миграции
echo 🚀 Запуск миграции...
python migrate_to_postgres_simple.py

echo.
echo ========================================
echo Миграция завершена
echo ========================================
pause
