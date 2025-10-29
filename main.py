import logging
import os
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from dotenv import load_dotenv
load_dotenv()  # Загружает переменные из .env файла
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from database.DataBase import init_db, get_user_by_id
from anketa_launcher import register_anketa_handlers
from handlers.navigation import show_menu, handle_navigation
from handlers.training import register_training_handlers
from handlers.training_check import (
    check_training_completion, 
    check_training_completion_next_day,
    handle_training_completion_response,
    handle_pain_feedback,
    reset_unanswered_sessions,
    handle_check_response,
    handle_check02_response
)
from utils.states import MENU_STATE

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получение токена из переменной окружения
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start - показывает главное меню"""
    return await show_menu(update, context)


async def handle_training_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ответы о выполнении тренировки и чеки"""
    text = update.message.text.lower()
    check_step = context.user_data.get('check_step')
    
    # Обработка чека
    if check_step == 'check01':
        if "да" in text or "✅" in text:
            await handle_check_response(update, context, True)
        elif "нет" in text or "❌" in text:
            await handle_check_response(update, context, False)
        return None
    elif check_step == 'check02':
        await handle_check02_response(update, context, update.message.text)
        return None
    
    # Обработка ответов о тренировке
    if "да, выполнил" in text or ("✅" in text and "да" in text):
        await handle_training_completion_response(update, context, True)
    elif "нет, не выполнил" in text or ("❌" in text and "нет" in text):
        await handle_training_completion_response(update, context, False)
    elif any(pain in text for pain in ["здоров", "болит рука", "болит спина", "болят ноги"]):
        pain_type = update.message.text
        await handle_pain_feedback(update, context, pain_type)
    else:
        # Если не распознано, отправляем в обычную навигацию
        return await handle_navigation(update, context)
    
    return None


def main():
    # Проверка наличия токена
    if not BOT_TOKEN:
        raise ValueError("Токен бота не найден! Установите переменную окружения TELEGRAM_BOT_TOKEN")

    init_db()
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    register_anketa_handlers(application)
    register_training_handlers(application)
    
    # Добавляем обработчик ответов о тренировках (должен быть перед навигацией)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(r"(✅|❌|Да|Нет|Здоров|Болит рука|Болит спина|Болят ноги)"),
        handle_training_response
    ))
    
    # Добавляем обработчик навигации для текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_navigation))
    
    # Настраиваем планировщик задач
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_training_completion,
        trigger=CronTrigger(hour=23, minute=0),
        args=[application],
        id='check_training_23',
        replace_existing=True
    )
    scheduler.add_job(
        check_training_completion_next_day,
        trigger=CronTrigger(hour=16, minute=0),
        args=[application],
        id='check_training_16',
        replace_existing=True
    )
    scheduler.add_job(
        reset_unanswered_sessions,
        trigger=CronTrigger(hour=23, minute=59),
        args=[application],
        id='reset_unanswered',
        replace_existing=True
    )
    
    print("Бот запущен...")
    
    # Запускаем планировщик после создания event loop
    async def start_scheduler():
        scheduler.start()
    
    # Добавляем задачу запуска планировщика
    application.job_queue.run_once(lambda context: asyncio.create_task(start_scheduler()), when=1)
    
    application.run_polling()


if __name__ == "__main__":
    main()