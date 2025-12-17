from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from database.DataBase import create_training_session, get_active_training_session, update_training_session
from utils.texts import text04
from Keyboards.keyboards import main_keyboard


async def handle_training_days_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор дней тренировок"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    data = query.data
    
    # Маппинг callback_data на дни недели
    days_mapping = {
        "days_mon_wed_fri": "Пн-Ср-Пт",
        "days_tue_thu_sat": "Вт-Чт-Сб", 
        "days_wed_fri_sun": "Ср-Пт-Вс"
    }
    
    training_days = days_mapping.get(data)
    if not training_days:
        await query.edit_message_text("❌ Ошибка выбора дней")
        return
    
    # Создаем новую тренировочную сессию
    session_id = create_training_session(user.id, 1, training_days)
    
    # Показываем план тренировок
    await query.edit_message_text(
        f"✅ Дни тренировок выбраны: {training_days}\n\n"
        f"{text04}",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Начать тренировки", callback_data="start_training")
        ]])
    )


async def start_training(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает тренировочный процесс"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    session = get_active_training_session(user.id)
    
    if not session:
        await query.edit_message_text("❌ Ошибка: тренировочная сессия не найдена")
        return
    
    # Показываем статус и возвращаемся в главное меню
    from handlers.navigation import show_training_status
    await show_training_status(update, context, session)


async def skip_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ВРЕМЕННАЯ ФУНКЦИЯ: Скипает день для тестирования"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    session = get_active_training_session(user.id)
    
    if not session:
        await query.edit_message_text("❌ Ошибка: тренировочная сессия не найдена")
        return
    
    session_id = session[0]
    current_day = session[4]
    completed_days = session[5]
    week_num = session[2]
    
    # Увеличиваем счетчики
    new_completed_days = completed_days + 1
    new_current_day = (current_day + 1) % 3
    
    # Обновляем сессию
    update_training_session(
        session_id,
        current_day=new_current_day,
        completed_days=new_completed_days
    )
    
    # Проверяем, завершена ли неделя
    if new_completed_days >= 3:
        # Неделя завершена - показываем сообщение о завершении
        from handlers.training_check import handle_week_completion
        await handle_week_completion(update, context, session)
    else:
        # Показываем обновленный статус
        from handlers.navigation import show_training_status
        # Обновляем сессию в контексте
        updated_session = get_active_training_session(user.id)
        await show_training_status(update, context, updated_session)


async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает текущий статус тренировок"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    session = get_active_training_session(user.id)
    
    if not session:
        await query.edit_message_text("❌ Ошибка: тренировочная сессия не найдена")
        return
    
    from handlers.navigation import show_training_status
    await show_training_status(update, context, session)


def register_training_handlers(application):
    """Регистрирует обработчики для тренировочного процесса"""
    application.add_handler(CallbackQueryHandler(handle_training_days_selection, pattern="^days_"))
    application.add_handler(CallbackQueryHandler(start_training, pattern="^start_training$"))
    application.add_handler(CallbackQueryHandler(skip_day, pattern="^skip_day$"))
    application.add_handler(CallbackQueryHandler(show_status, pattern="^show_status$"))
