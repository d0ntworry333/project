from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from utils.states import (
    HEIGHT,
    WEIGHT,
    ACTIVITY_LEVEL,
    GENDER,
    YEARS_EXPERIENCE,
    GOAL,
    SHORT_WEIGHT,
    SHORT_ACTIVITY_LEVEL,
    MAIN_STATE,
)
from utils.calculations import compute_brm, parse_height, parse_weight, validate_activity, normalize_gender, parse_age
from database.DataBase import save_user_to_db, get_user_by_id, has_user_forms, get_user_first_form
from utils.texts import text01, text02
from Keyboards.keyboards import *


async def start_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    
    # Проверяем, есть ли у пользователя уже анкеты
    if has_user_forms(user.id):
        # Если есть, начинаем краткую анкету
        await update.message.reply_text(
            "📝 Обновление анкеты!\n"
            "Введите ваш текущий вес (в кг):"
        )
        return SHORT_WEIGHT
    else:
        # Если нет, начинаем полную анкету
        await update.message.reply_text(
            "Давайте заполним анкету! 📝\nПожалуйста, введите ваш рост (в см):"
        )
        return HEIGHT


async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    height = parse_height(update.message.text)
    if height is None:
        await update.message.reply_text("Пожалуйста, введите реальный рост (50-250 см):")
        return HEIGHT
    context.user_data['height'] = height
    await update.message.reply_text("Введите ваш вес (в кг):")
    return WEIGHT


async def get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    weight = parse_weight(update.message.text)
    if weight is None:
        await update.message.reply_text("Пожалуйста, введите реальный вес (20-300 кг):")
        return WEIGHT
    context.user_data['weight'] = weight

    activity_keyboard = [
        [KeyboardButton("Очень высокая"), KeyboardButton("Высокая")],
        [KeyboardButton("Средняя"), KeyboardButton("Низкая")],
        [KeyboardButton("/cancel")]
    ]
    reply_markup = ReplyKeyboardMarkup(activity_keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите ваш уровень активности:", reply_markup=reply_markup)
    return ACTIVITY_LEVEL


async def get_activity_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    activity_level = validate_activity(update.message.text)
    if activity_level is None:
        await update.message.reply_text("Пожалуйста, выберите один из предложенных вариантов:")
        return ACTIVITY_LEVEL
    context.user_data['activity_level'] = activity_level

    gender_keyboard = [
        [KeyboardButton("Мужской"), KeyboardButton("Женский")],
        [KeyboardButton("/cancel")]
    ]
    reply_markup = ReplyKeyboardMarkup(gender_keyboard, resize_keyboard=True)
    await update.message.reply_text("Укажите ваш пол:", reply_markup=reply_markup)
    return GENDER


async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gender = normalize_gender(update.message.text)
    if gender is None:
        await update.message.reply_text("Пожалуйста, укажите пол кнопкой: Мужской или Женский")
        return GENDER
    context.user_data['gender'] = gender
    await update.message.reply_text("Сколько вам полных лет?")
    return YEARS_EXPERIENCE


async def get_years_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    years = parse_age(update.message.text)
    if years is None:
        await update.message.reply_text("Пожалуйста, введите реальный возраст (1-120 лет):")
        return YEARS_EXPERIENCE
    context.user_data['years_experience'] = years

    goal_keyboard = [
        [KeyboardButton("Снизить вес (дефицит)"), KeyboardButton("Набрать вес (профицит)")],
        [KeyboardButton("/cancel")]
    ]
    reply_markup = ReplyKeyboardMarkup(goal_keyboard, resize_keyboard=True)
    await update.message.reply_text("Какова ваша цель? Выберите один вариант:", reply_markup=reply_markup)
    return GOAL


async def get_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    goal_text = update.message.text
    if "снизить" in goal_text.lower():
        context.user_data['goal'] = "дефицит"
    elif "набрать" in goal_text.lower():
        context.user_data['goal'] = "профицит"
    else:
        await update.message.reply_text("Пожалуйста, выберите один из предложенных вариантов: снизить или набрать вес")
        return GOAL

    user = update.message.from_user

    brm_value = compute_brm(
        weight_kg=float(context.user_data['weight']),
        height_cm=float(context.user_data['height']),
        age_years=int(context.user_data['years_experience']),
        activity_level_text=str(context.user_data['activity_level']),
        gender_text=str(context.user_data['gender'])
    )

    user_data = {
        'user_id': user.id,
        'username': user.username,
        'height': context.user_data['height'],
        'weight': context.user_data['weight'],
        'activity_level': context.user_data['activity_level'],
        'gender': context.user_data['gender'],
        'years_experience': context.user_data['years_experience'],
        'goal': context.user_data['goal'],
        'brm': brm_value,
    }

    save_user_to_db(user_data)

    saved_user = get_user_by_id(user.id)

    from Keyboards.keyboards import main_keyboard
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "✅ Анкета успешно сохранена!\n"
        f"📅 Дата заполнения: {saved_user[8]}\n\n"
        "Ваши данные:\n"
        f"📏 Рост: {context.user_data['height']} см\n"
        f"⚖️ Вес: {context.user_data['weight']} кг\n"
        f"🏃 Уровень активности: {context.user_data['activity_level']}\n"
        f"👤 Пол: {context.user_data['gender']}\n"
        f"🎂 Возраст: {context.user_data['years_experience']} лет\n"
        f"🎯 Цель: {context.user_data['goal']}",
        reply_markup=reply_markup
    )

    try:
        if context.user_data['goal'] == 'дефицит':
            await update.message.reply_text(text01)
        else:
            await update.message.reply_text(text02)
    except Exception:
        pass

    # Очищаем данные анкеты, но сохраняем состояние
    context.user_data.clear()
    # Устанавливаем состояние главного меню после очистки
    context.user_data['current_state'] = MAIN_STATE
    return ConversationHandler.END


async def get_short_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка веса для краткой анкеты"""
    weight = parse_weight(update.message.text)
    if weight is None:
        await update.message.reply_text("Пожалуйста, введите реальный вес (20-300 кг):")
        return SHORT_WEIGHT
    context.user_data['weight'] = weight

    activity_keyboard = [
        [KeyboardButton("Очень высокая"), KeyboardButton("Высокая")],
        [KeyboardButton("Средняя"), KeyboardButton("Низкая")],
        [KeyboardButton("/cancel")]
    ]
    reply_markup = ReplyKeyboardMarkup(activity_keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите ваш текущий уровень активности:", reply_markup=reply_markup)
    return SHORT_ACTIVITY_LEVEL


async def get_short_activity_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка уровня активности для краткой анкеты"""
    activity_level = validate_activity(update.message.text)
    if activity_level is None:
        await update.message.reply_text("Пожалуйста, выберите один из предложенных вариантов:")
        return SHORT_ACTIVITY_LEVEL
    context.user_data['activity_level'] = activity_level

    user = update.message.from_user
    
    # Получаем первую анкету пользователя для копирования остальных данных
    first_form = get_user_first_form(user.id)
    if not first_form:
        await update.message.reply_text("Ошибка: не найдена первая анкета. Попробуйте заполнить полную анкету.")
        return ConversationHandler.END

    # Вычисляем новый BRM с обновленными данными
    brm_value = compute_brm(
        weight_kg=float(context.user_data['weight']),
        height_cm=float(first_form[3]),  # рост из первой анкеты
        age_years=int(first_form[7]),    # возраст из первой анкеты
        activity_level_text=str(context.user_data['activity_level']),
        gender_text=str(first_form[6])   # пол из первой анкеты
    )

    # Сохраняем краткую анкету с данными из первой анкеты
    user_data = {
        'user_id': user.id,
        'username': user.username,
        'height': first_form[3],  # рост из первой анкеты
        'weight': context.user_data['weight'],
        'activity_level': context.user_data['activity_level'],
        'gender': first_form[6],  # пол из первой анкеты
        'years_experience': first_form[7],  # возраст из первой анкеты
        'goal': first_form[9],    # цель из первой анкеты
        'brm': brm_value,
    }

    save_user_to_db(user_data)

    from Keyboards.keyboards import main_keyboard
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "✅ Анкета обновлена!\n\n"
        f"📏 Рост: {first_form[3]} см (из первой анкеты)\n"
        f"⚖️ Вес: {context.user_data['weight']} кг (обновлен)\n"
        f"🏃 Уровень активности: {context.user_data['activity_level']} (обновлен)\n"
        f"👤 Пол: {first_form[6]} (из первой анкеты)\n"
        f"🎂 Возраст: {first_form[7]} лет (из первой анкеты)\n"
        f"🎯 Цель: {first_form[9]} (из первой анкеты)",
        reply_markup=reply_markup
    )

    # Очищаем данные анкеты, но сохраняем состояние
    context.user_data.clear()
    # Устанавливаем состояние главного меню после очистки
    context.user_data['current_state'] = MAIN_STATE
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Очищаем данные анкеты, но сохраняем состояние
    context.user_data.clear()
    # Устанавливаем состояние главного меню после очистки
    context.user_data['current_state'] = MAIN_STATE
    from Keyboards.keyboards import main_keyboard
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text("Заполнение анкеты отменено.", reply_markup=reply_markup)
    return ConversationHandler.END


