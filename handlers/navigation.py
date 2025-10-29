from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from utils.states import MENU_STATE, MAIN_STATE, ANKETA_STATE
from Keyboards.keyboards import menu_keyboard, main_keyboard, anketa_keyboard
from database.DataBase import get_user_by_id, get_active_training_session, advance_to_next_week, update_training_session
from utils.texts import text01, text02, text03


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает главное меню (состояние 0)"""
    context.user_data['current_state'] = MENU_STATE
    reply_markup = ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🏠 Главное меню\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )
    return MENU_STATE


async def show_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает основное меню (состояние 1)"""
    context.user_data['current_state'] = MAIN_STATE
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "📋 Основное меню\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )
    return MAIN_STATE


async def show_anketa_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню анкеты (состояние 2)"""
    context.user_data['current_state'] = ANKETA_STATE
    reply_markup = ReplyKeyboardMarkup(anketa_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "📝 Меню анкеты\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )
    return ANKETA_STATE


async def show_goal_and_diet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает цель пользователя и план питания"""
    user = update.message.from_user
    user_data = get_user_by_id(user.id)
    
    if not user_data:
        await update.message.reply_text(
            "❌ У вас еще нет заполненной анкеты.\n"
            "Сначала заполните анкету, чтобы получить персональные рекомендации."
        )
        return MAIN_STATE
    
    # Показываем цель пользователя
    goal_text = f"🎯 Ваша цель: {user_data[9]}\n\n"
    
    # Показываем план питания в зависимости от цели
    if user_data[9] == 'дефицит':
        diet_text = text01
    else:
        diet_text = text02
    
    full_text = goal_text + diet_text
    
    # Отправляем сообщение с кнопкой возврата
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        full_text,
        reply_markup=reply_markup
    )
    return MAIN_STATE


async def handle_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает навигацию между состояниями"""
    text = update.message.text.lower()
    current_state = context.user_data.get('current_state', MENU_STATE)
    
    # Обработка команд из анкеты - эти команды обрабатываются в anketa_launcher.py
    # Просто возвращаем текущее состояние
    
    if text == "main":
        if current_state == MENU_STATE:
            return await show_main(update, context)
        elif current_state == ANKETA_STATE:
            return await show_main(update, context)
    
    elif text == "questionnaire":
        if current_state == MAIN_STATE:
            return await show_anketa_menu(update, context)
    
    elif text == "return":
        if current_state == ANKETA_STATE:
            return await show_main(update, context)
    
    elif text == "main menu":
        if current_state == MAIN_STATE:
            return await show_menu(update, context)
    
    elif text == "goal & diet":
        if current_state == MAIN_STATE:
            return await show_goal_and_diet(update, context)
    
    elif text == "recovery recommendations":
        if current_state == MAIN_STATE:
            reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
            await update.message.reply_text(
                text03,
                reply_markup=reply_markup
            )
            return current_state
    
    elif text == "training process":
        if current_state == MAIN_STATE:
            user = update.message.from_user
            # Проверяем, есть ли активная тренировочная сессия
            from database.DataBase import get_active_training_session
            session = get_active_training_session(user.id)
            
            if session:
                # Если есть активная сессия, показываем текущий статус
                await show_training_status(update, context, session)
            else:
                # Если нет активной сессии, начинаем выбор дней
                await start_training_process(update, context)
            return current_state
    
    elif text == "/achievements":
        if current_state == MENU_STATE:
            await update.message.reply_text(
                "🏆 Достижения пока в разработке.\n"
                "Скоро будет доступно!"
            )
            return current_state
    
    elif text == "следующая неделя":
        if current_state == ANKETA_STATE:
            return await handle_next_week(update, context)
    
    # Обработка кнопок тренировочного процесса
    elif text == "📋 упражнения дня":
        return await show_today_exercises(update, context)
    
    elif text == "📅 расписание":
        return await show_training_schedule(update, context)
    
    elif text == "⏭️ скип дня":
        return await handle_skip_day_button(update, context)
    
    elif text == "📊 статус":
        return await show_training_status_button(update, context)
    
    elif text == "🏠 главное меню":
        return await show_main(update, context)
    
    elif text == "⏸️ пропустить день (тест)":
        return await handle_skip_day_missed(update, context)
    
    elif text == "⬅️ предыдущая неделя":
        return await handle_previous_week(update, context)
    
    elif text == "➡️ следующая неделя":
        return await handle_next_week_from_training(update, context)
    
    # Если команда не распознана, остаемся в текущем состоянии
    return current_state


async def start_training_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс выбора дней тренировок"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton("Пн-Ср-Пт", callback_data="days_mon_wed_fri")],
        [InlineKeyboardButton("Вт-Чт-Сб", callback_data="days_tue_thu_sat")],
        [InlineKeyboardButton("Ср-Пт-Вс", callback_data="days_wed_fri_sun")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🏋️ Выберите дни для тренировок:\n\n"
        "Выберите один из вариантов (между днями должен быть промежуток в 1 день):",
        reply_markup=reply_markup
    )


async def show_training_status(update: Update, context: ContextTypes.DEFAULT_TYPE, session):
    """Показывает текущий статус тренировочной сессии"""
    week_num = session[2]
    training_days = session[3]
    current_day = session[4]
    completed_days = session[5]
    
    status_text = f"📊 Статус тренировок (Неделя {week_num}):\n\n"
    status_text += f"📅 Дни тренировок: {training_days}\n"
    status_text += f"✅ Выполнено дней: {completed_days}/3\n"
    status_text += f"📋 Текущий день: {current_day + 1}\n\n"
    
    if completed_days == 3:
        status_text += "🎉 Неделя завершена! Ожидайте чека."
    else:
        status_text += "💪 Продолжайте тренировки!"
    
    # Используем новую тренировочную клавиатуру
    from Keyboards.keyboards import training_keyboard
    reply_markup = ReplyKeyboardMarkup(training_keyboard, resize_keyboard=True)
    
    # Проверяем, это callback query или message
    if update.callback_query:
        await update.callback_query.edit_message_text(status_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(status_text, reply_markup=reply_markup)


async def handle_next_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает переход на следующую неделю"""
    user = update.message.from_user
    
    # Проверяем, есть ли активная тренировочная сессия
    session = get_active_training_session(user.id)
    if not session:
        await update.message.reply_text(
            "❌ У вас нет активной тренировочной сессии.\n"
            "Сначала запустите тренировочный процесс."
        )
        return ANKETA_STATE
    
    # Переводим на следующую неделю
    new_week = advance_to_next_week(user.id)
    if new_week:
        await update.message.reply_text(
            f"📅 Переходим к неделе {new_week}!\n\n"
            "Сначала обновим ваши параметры в анкете."
        )
        
        # Запускаем анкету для обновления параметров
        from handlers.form import start_form
        return await start_form(update, context)
    else:
        await update.message.reply_text(
            "❌ Ошибка при переходе на следующую неделю."
        )
        return ANKETA_STATE


async def show_today_exercises(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает упражнения для текущего дня"""
    user = update.message.from_user
    session = get_active_training_session(user.id)
    
    if not session:
        await update.message.reply_text("❌ У вас нет активной тренировочной сессии.")
        return
    
    current_day = session[4]
    week_num = session[2]
    
    # Определяем тип тренировки по дню
    training_types = ["День 1: Грудь, Плечи, Трицепс", "День 2: Спина, Бицепс", "День 3: Ноги и Кор"]
    training_type = training_types[current_day]
    
    # Показываем упражнения (пока используем text04)
    from utils.texts import text04
    from Keyboards.keyboards import training_keyboard
    reply_markup = ReplyKeyboardMarkup(training_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"📋 {training_type} (Неделя {week_num})\n\n"
        f"{text04}",
        reply_markup=reply_markup
    )


async def show_training_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает расписание тренировок"""
    user = update.message.from_user
    session = get_active_training_session(user.id)
    
    if not session:
        await update.message.reply_text("❌ У вас нет активной тренировочной сессии.")
        return
    
    week_num = session[2]
    training_days = session[3]
    current_day = session[4]
    completed_days = session[5]
    
    schedule_text = f"📅 Расписание тренировок (Неделя {week_num}):\n\n"
    schedule_text += f"📆 Дни тренировок: {training_days}\n\n"
    
    # Показываем каждый день
    training_types = ["День 1: Грудь, Плечи, Трицепс", "День 2: Спина, Бицепс", "День 3: Ноги и Кор"]
    for i, day_type in enumerate(training_types):
        status = "✅" if i < completed_days else "⏳" if i == current_day else "⭕"
        schedule_text += f"{status} {day_type}\n"
    
    from Keyboards.keyboards import training_keyboard
    reply_markup = ReplyKeyboardMarkup(training_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(schedule_text, reply_markup=reply_markup)


async def handle_skip_day_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает кнопку скипа дня"""
    user = update.message.from_user
    session = get_active_training_session(user.id)
    
    if not session:
        await update.message.reply_text("❌ У вас нет активной тренировочной сессии.")
        return
    
    session_id = session[0]
    current_day = session[4]
    completed_days = session[5]
    
    # Увеличиваем счетчики
    new_completed_days = completed_days + 1
    new_current_day = (current_day + 1) % 3
    
    # Обновляем сессию
    update_training_session(
        session_id,
        current_day=new_current_day,
        completed_days=new_completed_days
    )
    
    # Спрашиваем о боли (как при реальном выполнении)
    keyboard = [
        [KeyboardButton("Здоров"), KeyboardButton("Болит рука")],
        [KeyboardButton("Болит спина"), KeyboardButton("Болят ноги")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "💪 День выполнен!\n\n"
        "Болело ли что-то во время тренировки?",
        reply_markup=reply_markup
    )
    
    # Сохраняем в контексте для обработки ответа о боли
    context.user_data['training_log_id'] = 'skip_day'  # Маркер для скипа
    context.user_data['session_id'] = session_id


async def show_training_status_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статус тренировок по кнопке"""
    user = update.message.from_user
    session = get_active_training_session(user.id)
    
    if not session:
        await update.message.reply_text("❌ У вас нет активной тренировочной сессии.")
        return
    
    await show_training_status(update, context, session)


async def handle_skip_day_missed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ВРЕМЕННАЯ ФУНКЦИЯ: Обрабатывает пропуск дня (не выполнение тренировки)"""
    user = update.message.from_user
    session = get_active_training_session(user.id)
    
    if not session:
        await update.message.reply_text("❌ У вас нет активной тренировочной сессии.")
        return
    
    session_id = session[0]
    current_day = session[4]
    completed_days = session[5]
    week_num = session[2]
    
    # Определяем тип тренировки, которая была пропущена
    training_types = ["День 1: Грудь, Плечи, Трицепс", "День 2: Спина, Бицепс", "День 3: Ноги и Кор"]
    missed_training = training_types[current_day]
    
    # НЕ сдвигаем current_day - тренировка остается той же самой
    # Только отмечаем, что день был пропущен (можно добавить поле в БД для отслеживания пропусков)
    
    # Обновляем сессию - НЕ меняем current_day и completed_days
    # Тренировка остается той же самой для выполнения
    update_training_session(
        session_id,
        current_day=current_day,  # Остается тот же день
        completed_days=completed_days  # Не увеличиваем!
    )
    
    # Показываем сообщение о пропуске
    from Keyboards.keyboards import training_keyboard
    reply_markup = ReplyKeyboardMarkup(training_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"⏸️ День пропущен!\n\n"
        f"Пропущена тренировка: {missed_training}\n\n"
        f"⚠️ ВАЖНО: Эта тренировка все еще должна быть выполнена!\n"
        f"Она не переносится на следующий день.\n\n"
        f"Текущий прогресс: {completed_days}/3 дней выполнено.\n"
        f"Следующая тренировка: {missed_training}",
        reply_markup=reply_markup
    )
    
    # Показываем обновленный статус
    updated_session = get_active_training_session(user.id)
    if updated_session:
        await show_training_status(update, context, updated_session)


async def handle_previous_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает переход на предыдущую неделю (для тестирования)"""
    user = update.message.from_user
    session = get_active_training_session(user.id)
    
    if not session:
        await update.message.reply_text("❌ У вас нет активной тренировочной сессии.")
        return
    
    session_id = session[0]
    current_week = session[2]
    
    if current_week <= 1:
        await update.message.reply_text("❌ Вы уже на первой неделе!")
        return
    
    # Уменьшаем номер недели
    new_week = current_week - 1
    update_training_session(
        session_id,
        week_number=new_week,
        completed_days=0,
        current_day=0,
        check02_passed=False
    )
    
    from Keyboards.keyboards import training_keyboard
    reply_markup = ReplyKeyboardMarkup(training_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"⬅️ Перешли на неделю {new_week}!\n\n"
        "Счетчики сброшены. Можете начать заново.",
        reply_markup=reply_markup
    )


async def handle_next_week_from_training(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает переход на следующую неделю из тренировочного процесса"""
    user = update.message.from_user
    session = get_active_training_session(user.id)
    
    if not session:
        await update.message.reply_text("❌ У вас нет активной тренировочной сессии.")
        return
    
    # Переводим на следующую неделю
    new_week = advance_to_next_week(user.id)
    if new_week:
        from Keyboards.keyboards import training_keyboard
        reply_markup = ReplyKeyboardMarkup(training_keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f"➡️ Перешли на неделю {new_week}!\n\n"
            "Счетчики сброшены. Можете начать новую неделю.",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("❌ Ошибка при переходе на следующую неделю.")
