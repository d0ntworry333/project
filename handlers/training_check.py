import asyncio
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

from database.DataBase import (
    get_all_active_training_sessions, 
    add_training_log, 
    update_training_session,
    get_active_training_session,
    get_pending_training_check
)
from Keyboards.keyboards import main_keyboard


# Маппинг дней недели
DAYS_MAPPING = {
    "Пн-Ср-Пт": [0, 2, 4],  # Понедельник, Среда, Пятница
    "Вт-Чт-Сб": [1, 3, 5],  # Вторник, Четверг, Суббота
    "Ср-Пт-Вс": [2, 4, 6],  # Среда, Пятница, Воскресенье
}

# Типы тренировок по дням
TRAINING_TYPES = ["День 1: Грудь, Плечи, Трицепс", "День 2: Спина, Бицепс", "День 3: Ноги и Кор"]


def get_day_of_week():
    """Возвращает текущий день недели (0=Понедельник, 6=Воскресенье)"""
    return datetime.now().weekday()


def is_training_day(training_days_str: str, today: int = None):
    """Проверяет, является ли сегодня день тренировки"""
    if today is None:
        today = get_day_of_week()
    
    training_days = DAYS_MAPPING.get(training_days_str)
    if training_days:
        return today in training_days
    return False


def get_training_day_number(training_days_str: str, today: int = None):
    """Возвращает номер дня тренировки (0, 1 или 2)"""
    if today is None:
        today = get_day_of_week()
    
    training_days = DAYS_MAPPING.get(training_days_str)
    if training_days:
        try:
            return training_days.index(today)
        except ValueError:
            return None
    return None


async def check_training_completion(application):
    """Проверяет выполнение тренировок в 23:00"""
    sessions = get_all_active_training_sessions()
    today = datetime.now().date()
    today_str = today.strftime('%Y-%m-%d')
    
    for session in sessions:
        user_id = session[1]
        session_id = session[0]
        training_days_str = session[3]
        current_day = session[4]
        completed_days = session[5]
        
        # Проверяем, является ли сегодня день тренировки
        if not is_training_day(training_days_str):
            continue
        
        # Проверяем, была ли уже создана запись о тренировке сегодня
        existing_log = get_pending_training_check(user_id, today_str)
        if existing_log:
            continue
        
        # Определяем тип тренировки
        training_day_num = get_training_day_number(training_days_str)
        if training_day_num is None:
            continue
        
        training_type = TRAINING_TYPES[training_day_num]
        
        # Создаем запись о тренировке
        add_training_log(user_id, session_id, today_str, training_type, None)
        
        # Отправляем сообщение пользователю
        keyboard = [
            [KeyboardButton("✅ Да, выполнил"), KeyboardButton("❌ Нет, не выполнил")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await application.bot.send_message(
            chat_id=user_id,
            text=f"🏋️ Выполнили ли вы тренировку сегодня?\n\n"
                 f"Тренировка: {training_type}",
            reply_markup=reply_markup
        )


async def check_training_completion_next_day(application):
    """Проверяет выполнение тренировок на следующий день в 16:00"""
    sessions = get_all_active_training_sessions()
    yesterday = (datetime.now() - timedelta(days=1)).date()
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    
    for session in sessions:
        user_id = session[1]
        session_id = session[0]
        training_days_str = session[3]
        
        # Проверяем, был ли вчера день тренировки
        yesterday_weekday = yesterday.weekday()
        if not is_training_day(training_days_str, yesterday_weekday):
            continue
        
        # Проверяем, была ли уже проверка или ответ
        pending_log = get_pending_training_check(user_id, yesterday_str)
        if not pending_log:
            continue
        
        # Отправляем напоминание
        keyboard = [
            [KeyboardButton("✅ Да, выполнил"), KeyboardButton("❌ Нет, не выполнил")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await application.bot.send_message(
            chat_id=user_id,
            text=f"🏋️ Напоминание: выполнили ли вы тренировку вчера?\n\n"
                 f"Тренировка: {pending_log[4]}",
            reply_markup=reply_markup
        )


async def handle_training_completion_response(update: Update, context: ContextTypes.DEFAULT_TYPE, completed: bool):
    """Обрабатывает ответ пользователя о выполнении тренировки"""
    user = update.message.from_user
    text = update.message.text.lower()
    
    # Определяем дату тренировки
    session = get_active_training_session(user.id)
    if not session:
        await update.message.reply_text("❌ Тренировочная сессия не найдена")
        return
    
    # Ищем последнюю непроверенную тренировку
    today = datetime.now().date()
    today_str = today.strftime('%Y-%m-%d')
    
    pending_log = get_pending_training_check(user.id, today_str)
    if not pending_log:
        # Проверяем вчерашнюю тренировку
        yesterday = (datetime.now() - timedelta(days=1)).date()
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        pending_log = get_pending_training_check(user.id, yesterday_str)
    
    if not pending_log:
        await update.message.reply_text("❌ Тренировка не найдена")
        return
    
    session_id = session[0]
    training_type = pending_log[4]
    
    if completed:
        # Тренировка выполнена - спрашиваем о боли
        keyboard = [
            [KeyboardButton("Здоров"), KeyboardButton("Болит рука")],
            [KeyboardButton("Болит спина"), KeyboardButton("Болят ноги")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "💪 Отлично! Выполнили тренировку!\n\n"
            "Болело ли что-то во время тренировки?",
            reply_markup=reply_markup
        )
        
        # Сохраняем в контексте для следующего шага
        context.user_data['training_log_id'] = pending_log[0]
        context.user_data['training_type'] = training_type
        context.user_data['session_id'] = session_id
    else:
        # Тренировка не выполнена - переносим на следующий день
        await handle_training_postponement(update, context, session, training_type)
    
    # Обновляем запись в базе
    import sqlite3
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE training_log 
        SET completed = ? 
        WHERE id = ?
    ''', (completed, pending_log[0]))
    conn.commit()
    conn.close()


async def handle_training_postponement(update: Update, context: ContextTypes.DEFAULT_TYPE, session, training_type: str):
    """Обрабатывает перенос тренировки на следующий день"""
    session_id = session[0]
    training_days_str = session[3]
    current_day = session[4]
    completed_days = session[5]
    
    # Переносим тренировку на следующий день
    # Просто увеличиваем current_day, но не completed_days
    # Следующая тренировка будет того же типа, что и текущая
    
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"📅 Тренировка перенесена на следующий день.\n\n"
        f"Не забудьте выполнить: {training_type}",
        reply_markup=reply_markup
    )


async def handle_pain_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE, pain_type: str):
    """Обрабатывает ответ о боли после тренировки"""
    user = update.message.from_user
    training_log_id = context.user_data.get('training_log_id')
    
    if not training_log_id:
        await update.message.reply_text("❌ Ошибка обработки")
        return
    
    # Пока только "Здоров" работает
    if pain_type.lower() != "здоров":
        await update.message.reply_text(
            "🚧 Функция адаптации тренировки под боль пока в разработке.\n"
            "Спасибо за информацию!"
        )
        return
    
    # Если это скип дня, не обновляем базу логов
    if training_log_id != 'skip_day':
        # Обновляем запись в базе
        import sqlite3
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE training_log 
            SET pain_feedback = ? 
            WHERE id = ?
        ''', (pain_type, training_log_id))
        conn.commit()
        conn.close()
    
    # Если это скип дня, счетчики уже обновлены, просто проверяем завершение недели
    if training_log_id == 'skip_day':
        session_id = context.user_data.get('session_id')
        session = get_active_training_session(user.id)
        if session:
            completed_days = session[5]
            
            # Проверяем, завершена ли неделя (3 тренировки подряд)
            if completed_days >= 3:
                await handle_week_completion(update, context, session)
            else:
                # Показываем обновленный статус с тренировочной клавиатурой
                from Keyboards.keyboards import training_keyboard
                reply_markup = ReplyKeyboardMarkup(training_keyboard, resize_keyboard=True)
                await update.message.reply_text(
                    "✅ Отлично! Тренировка засчитана.\n\n"
                    "Продолжайте в том же духе! 💪",
                    reply_markup=reply_markup
                )
    else:
        # Обычная тренировка - увеличиваем счетчики
        session_id = context.user_data.get('session_id')
        session = get_active_training_session(user.id)
        if session:
            completed_days = session[5]
            current_day = session[4]
            
            # Увеличиваем completed_days если это новая тренировка
            update_training_session(
                session_id,
                completed_days=completed_days + 1,
                current_day=(current_day + 1) % 3
            )
            
            # Проверяем, завершена ли неделя (3 тренировки подряд)
            if completed_days + 1 >= 3:
                await handle_week_completion(update, context, session)
            else:
                # Показываем обновленный статус с тренировочной клавиатурой
                from Keyboards.keyboards import training_keyboard
                reply_markup = ReplyKeyboardMarkup(training_keyboard, resize_keyboard=True)
                await update.message.reply_text(
                    "✅ Отлично! Тренировка засчитана.\n\n"
                    "Продолжайте в том же духе! 💪",
                    reply_markup=reply_markup
                )
    
    # Очищаем контекст
    context.user_data.pop('training_log_id', None)
    context.user_data.pop('training_type', None)
    context.user_data.pop('session_id', None)


async def handle_week_completion(update: Update, context: ContextTypes.DEFAULT_TYPE, session):
    """Обрабатывает завершение недели тренировок"""
    week_num = session[2]
    session_id = session[0]
    check01_passed = session[7]
    check02_passed = session[8]
    
    await update.message.reply_text(
        f"🎉 Неделя {week_num} выполнена!\n\n"
        f"📊 Информация о вашем теле (в разработке)\n\n"
    )
    
    # Проверяем, нужно ли проходить чеки
    if week_num == 2:
        # После второй недели нужно пройти check01 и check02
        if not check01_passed or not check02_passed:
            await handle_check_process(update, context, session)
        else:
            # Чеки уже пройдены - неделя завершена, ждем ручного перехода
            reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
            await update.message.reply_text(
                "✅ Неделя завершена! Все чеки пройдены.\n\n"
                "Для перехода к следующей неделе используйте кнопку 'Следующая неделя' в меню анкеты.",
                reply_markup=reply_markup
            )
    elif week_num > 2:
        # После третьей недели и далее спрашиваем только check02 и другие чеки
        # (check01 больше не спрашивается)
        if not check02_passed:
            await handle_check02_weekly(update, context, session)
        else:
            # check02 пройден - неделя завершена, ждем ручного перехода
            reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
            await update.message.reply_text(
                "✅ Неделя завершена! check02 пройден.\n\n"
                "Для перехода к следующей неделе используйте кнопку 'Следующая неделя' в меню анкеты.",
                reply_markup=reply_markup
            )
    else:
        # Первая неделя - неделя завершена, ждем ручного перехода
        reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "✅ Неделя завершена!\n\n"
            "Для перехода к следующей неделе используйте кнопку 'Следующая неделя' в меню анкеты.",
            reply_markup=reply_markup
        )


async def handle_check_process(update: Update, context: ContextTypes.DEFAULT_TYPE, session):
    """Обрабатывает процесс чека после второй недели (check01 и check02)"""
    session_id = session[0]
    check01_passed = session[7]
    check02_passed = session[8]
    
    if not check01_passed:
        # Показываем check01 (только после второй недели)
        keyboard = [
            [KeyboardButton("✅ Да"), KeyboardButton("❌ Нет")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "📋 Чек-лист 1:\n\n"
            "Выполнили ли вы все тренировки? (check01)",
            reply_markup=reply_markup
        )
        
        context.user_data['check_step'] = 'check01'
        context.user_data['session_id'] = session_id
    elif not check02_passed:
        # Показываем check02
        await update.message.reply_text(
            "📋 Чек-лист 2:\n\n"
            "Средняя калорийность (check02)\n"
            "Введите вашу среднюю калорийность за неделю:"
        )
        
        context.user_data['check_step'] = 'check02'
        context.user_data['session_id'] = session_id
    else:
        # Оба чека пройдены
        await update.message.reply_text(
            "✅ Все чеки пройдены!\n\n"
            "Можете продолжать тренировки."
        )


async def handle_check02_weekly(update: Update, context: ContextTypes.DEFAULT_TYPE, session):
    """Обрабатывает check02 для недель после второй (check01 больше не спрашивается)"""
    session_id = session[0]
    
    await update.message.reply_text(
        "📋 Чек-лист 2:\n\n"
        "Средняя калорийность (check02)\n"
        "Введите вашу среднюю калорийность за неделю:"
    )
    
    context.user_data['check_step'] = 'check02'
    context.user_data['session_id'] = session_id


async def handle_check_response(update: Update, context: ContextTypes.DEFAULT_TYPE, check_result: bool):
    """Обрабатывает ответ на check01"""
    user = update.message.from_user
    session_id = context.user_data.get('session_id')
    
    if not session_id:
        # Если нет session_id в контексте, пытаемся получить из сессии
        session = get_active_training_session(user.id)
        if session:
            session_id = session[0]
        else:
            await update.message.reply_text("❌ Ошибка обработки")
            return
    
    if check_result:
        # check01 пройден - переходим к check02
        update_training_session(session_id, check01_passed=True)
        
        # Переходим к check02
        await update.message.reply_text(
            "✅ Чек-лист 1 пройден!\n\n"
            "📋 Чек-лист 2:\n\n"
            "Средняя калорийность (check02)\n"
            "Введите вашу среднюю калорийность за неделю:"
        )
        
        context.user_data['check_step'] = 'check02'
    else:
        # check01 не пройден - начинаем неделю заново
        await update.message.reply_text(
            "⚠️ Чек-лист 1 не пройден.\n\n"
            "Нужно выполнить неделю заново (3 дня тренировок)."
        )
        
        # Сбрасываем счетчик выполненных дней
        update_training_session(session_id, completed_days=0, current_day=0)
        
        # Очищаем контекст
        context.user_data.pop('check_step', None)
        context.user_data.pop('session_id', None)


async def handle_check02_response(update: Update, context: ContextTypes.DEFAULT_TYPE, calories: str):
    """ВРЕМЕННАЯ ЗАПЛАТКА: Обрабатывает ответ на check02 (калорийность) - принимает любое значение"""
    user = update.message.from_user
    session_id = context.user_data.get('session_id')
    
    if not session_id:
        # Если нет session_id в контексте, пытаемся получить из сессии
        session = get_active_training_session(user.id)
        if session:
            session_id = session[0]
        else:
            await update.message.reply_text("❌ Ошибка обработки")
            return
    
    # Получаем текущую сессию для определения недели
    session = get_active_training_session(user.id)
    if not session:
        await update.message.reply_text("❌ Сессия не найдена")
        return
    
    week_num = session[2]
    
    # ВРЕМЕННАЯ ЗАПЛАТКА: принимаем любое значение (даже текст)
    calories_text = calories.strip()
    
    # check02 пройден
    update_training_session(session_id, check02_passed=True)
    
    # Очищаем контекст
    context.user_data.pop('check_step', None)
    context.user_data.pop('session_id', None)
    
    # Благодарим и пропускаем дальше
    from Keyboards.keyboards import training_keyboard
    reply_markup = ReplyKeyboardMarkup(training_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"✅ Спасибо! Данные о калорийности приняты.\n\n"
        f"📊 Введенное значение: {calories_text}\n\n"
        f"Чек-лист 2 пройден! Неделя завершена.",
        reply_markup=reply_markup
    )


async def reset_unanswered_sessions(application):
    """Сбрасывает сессии, на которые пользователь не ответил до конца следующего дня"""
    from datetime import datetime, timedelta
    sessions = get_all_active_training_sessions()
    two_days_ago = (datetime.now() - timedelta(days=2)).date()
    two_days_ago_str = two_days_ago.strftime('%Y-%m-%d')
    
    for session in sessions:
        user_id = session[1]
        session_id = session[0]
        
        # Проверяем, была ли тренировка 2 дня назад без ответа
        pending_log = get_pending_training_check(user_id, two_days_ago_str)
        if pending_log:
            # Сбрасываем сессию
            update_training_session(session_id, session_active=False)
            
            await application.bot.send_message(
                chat_id=user_id,
                text="⚠️ Тренировочная сессия сброшена из-за отсутствия ответа.\n\n"
                     "Запустите новый тренировочный процесс через меню."
            )
