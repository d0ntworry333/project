@echo off
chcp 65001 >nul
echo ========================================
echo    Запуск Telegram бота
echo ========================================
echo.

REM Проверка наличия виртуального окружения
if not exist ".venv\Scripts\activate.bat" (
    echo [ОШИБКА] Виртуальное окружение не найдено!
    echo Создайте его командой: python -m venv venv
    pause
    exit /b 1
)

REM Проверка наличия .env файла
if not exist ".env" (
    echo [ПРЕДУПРЕЖДЕНИЕ] Файл .env не найден!
    echo Создайте файл .env и добавьте в него: TELEGRAM_BOT_TOKEN=your_token_here
    echo.
    pause
)

REM Активация виртуального окружения и запуск бота
echo Активация виртуального окружения...
call venv\Scripts\activate.bat

echo.
echo Запуск бота...
echo.
python main.py

REM Если бот завершился, оставляем окно открытым
if errorlevel 1 (
    echo.
    echo [ОШИБКА] Бот завершился с ошибкой!
    pause
)

