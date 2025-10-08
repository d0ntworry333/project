import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import sqlite3
import datetime

# Расчет BRM по методике пользователя
def compute_brm(weight_kg: float, height_cm: float, age_years: int, activity_level_text: str, gender_text: str) -> float:
    # Маппинг уровня активности на коэффициент
    activity_map = {
        "Очень высокая": 1.725,  # эквивалентно very active
        "Высокая": 1.55,
        "Средняя": 1.375,
        "Низкая": 1.2,
    }

    activity = activity_map.get(activity_level_text, 1.2)

    gender = "man" if gender_text.lower().startswith("муж") or gender_text.lower() == "man" else "woman"

    if gender == 'man':
        brm = ((10 * weight_kg) + (6.25 * height_cm) - (5 * age_years) + 5) * activity
    else:
        brm = ((10 * weight_kg) + (6.25 * height_cm) - (5 * age_years) - 161) * activity

    return float(brm)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
HEIGHT, WEIGHT, ACTIVITY_LEVEL, GENDER, YEARS_EXPERIENCE, GOAL = range(6)


# Создаем базу данных и таблицу
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            height REAL,
            weight REAL,
            activity_level TEXT,
            gender TEXT,
            years_experience INTEGER,
            brm REAL,
            goal TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Создаем индекс для поиска по user_id
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_user_id ON users(user_id)
    ''')

    conn.commit()
    conn.close()


# Функция для сохранения пользователя в базу данных
def save_user_to_db(user_data):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Проверяем, есть ли уже анкета у пользователя
    cursor.execute('SELECT id FROM users WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
                   (user_data['user_id'],))
    existing_user = cursor.fetchone()

    # Расчет BRM для сохранения в БД
    brm_value = compute_brm(
        weight_kg=float(user_data['weight']),
        height_cm=float(user_data['height']),
        age_years=int(user_data['years_experience']),
        activity_level_text=str(user_data['activity_level']),
        gender_text=str(user_data['gender'])
    )

    if existing_user:
        # Обновляем существующую запись
        cursor.execute('''
            UPDATE users SET
            username = ?, height = ?, weight = ?, activity_level = ?, 
            gender = ?, years_experience = ?, brm = ?, goal = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            user_data['username'],
            user_data['height'],
            user_data['weight'],
            user_data['activity_level'],
            user_data['gender'],
            user_data['years_experience'],
            brm_value,
            user_data.get('goal'),
            existing_user[0]
        ))
    else:
        # Создаем новую запись
        cursor.execute('''
            INSERT INTO users 
            (user_id, username, height, weight, activity_level, gender, years_experience, brm, goal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_data['user_id'],
            user_data['username'],
            user_data['height'],
            user_data['weight'],
            user_data['activity_level'],
            user_data['gender'],
            user_data['years_experience'],
            brm_value,
            user_data.get('goal')
        ))

    conn.commit()
    conn.close()


# Функция для получения всех пользователей (последние анкеты каждого)
def get_all_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u1.* FROM users u1
        INNER JOIN (
            SELECT user_id, MAX(created_at) as max_date 
            FROM users 
            GROUP BY user_id
        ) u2 ON u1.user_id = u2.user_id AND u1.created_at = u2.max_date
        ORDER BY u1.created_at DESC
    ''')
    users = cursor.fetchall()
    conn.close()
    return users


# Функция для получения последней анкеты пользователя по ID
def get_user_by_id(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM users 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 1
    ''', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


# Функция для получения всех анкет пользователя
def get_all_user_forms(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM users 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (user_id,))
    forms = cursor.fetchall()
    conn.close()
    return forms


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    # Проверяем, есть ли у пользователя анкета
    user_data = get_user_by_id(user.id)

    welcome_text = (
        f"Привет, {user.first_name}! 👋\n"
        "Я бот для сбора антропометрических данных.\n\n"
        "Доступные команды:\n"
        "/form - начать заполнение анкеты\n"
        "/show_me - показать мою анкету\n"
        "/show_all - показать все анкеты\n"
        "/my_forms - показать все мои анкеты\n"
        "/cancel - отменить текущее действие"
    )

    if user_data:
        welcome_text += f"\n\n✅ У вас уже есть заполненная анкета от {user_data[8]}"
        welcome_text += "\nВы можете заполнить анкету повторно командой /form"

    await update.message.reply_text(welcome_text)


# Начало заполнения анкеты
async def start_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    # Проверяем, есть ли предыдущие анкеты
    previous_forms = get_all_user_forms(user.id)

    if previous_forms:
        await update.message.reply_text(
            "📝 Вы можете заполнить анкету повторно!\n"
            f"У вас уже {len(previous_forms)} заполненных анкет.\n"
            "Новая анкета будет добавлена в историю.\n\n"
            "Пожалуйста, введите ваш рост (в см):"
        )
    else:
        await update.message.reply_text(
            "Давайте заполним анкету! 📝\n"
            "Пожалуйста, введите ваш рост (в см):"
        )

    return HEIGHT


# Обработка роста
async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        height = float(update.message.text)
        if height < 50 or height > 250:
            await update.message.reply_text("Пожалуйста, введите реальный рост (50-250 см):")
            return HEIGHT
        context.user_data['height'] = height
        await update.message.reply_text("Введите ваш вес (в кг):")
        return WEIGHT
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число для роста:")
        return HEIGHT


# Обработка веса
async def get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        weight = float(update.message.text)
        if weight < 20 or weight > 300:
            await update.message.reply_text("Пожалуйста, введите реальный вес (20-300 кг):")
            return WEIGHT
        context.user_data['weight'] = weight

        # Клавиатура для уровня активности
        activity_keyboard = [
            [KeyboardButton("Очень высокая"), KeyboardButton("Высокая")],
            [KeyboardButton("Средняя"), KeyboardButton("Низкая")]
        ]
        reply_markup = ReplyKeyboardMarkup(activity_keyboard, resize_keyboard=True)

        await update.message.reply_text(
            "Выберите ваш уровень активности:",
            reply_markup=reply_markup
        )
        return ACTIVITY_LEVEL
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число для веса:")
        return WEIGHT


# Обработка уровня активности
async def get_activity_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    activity_level = update.message.text
    valid_levels = ["Очень высокая", "Высокая", "Средняя", "Низкая"]

    if activity_level not in valid_levels:
        await update.message.reply_text("Пожалуйста, выберите один из предложенных вариантов:")
        return ACTIVITY_LEVEL

    context.user_data['activity_level'] = activity_level

    # Клавиатура для пола
    gender_keyboard = [
        [KeyboardButton("Мужской"), KeyboardButton("Женский")]
    ]
    reply_markup = ReplyKeyboardMarkup(gender_keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Укажите ваш пол:",
        reply_markup=reply_markup
    )
    return GENDER


# Обработка пола
async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['gender'] = update.message.text
    await update.message.reply_text("Сколько вам полных лет?")
    return YEARS_EXPERIENCE


# Обработка возраста и сохранение данных
async def get_years_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        years = int(update.message.text)
        if years < 1 or years > 120:
            await update.message.reply_text("Пожалуйста, введите реальный возраст (1-120 лет):")
            return YEARS_EXPERIENCE

        context.user_data['years_experience'] = years
        # Спрашиваем цель (дефицит/профицит)
        goal_keyboard = [[KeyboardButton("Снизить вес (дефицит)"), KeyboardButton("Набрать вес (профицит)")]]
        reply_markup = ReplyKeyboardMarkup(goal_keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Какова ваша цель? Выберите один вариант:",
            reply_markup=reply_markup
        )
        return GOAL
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число для возраста:")
        return YEARS_EXPERIENCE
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

    # Сохраняем данные пользователя, включая цель
    user_data = {
        'user_id': user.id,
        'username': user.username,
        'height': context.user_data['height'],
        'weight': context.user_data['weight'],
        'activity_level': context.user_data['activity_level'],
        'gender': context.user_data['gender'],
        'years_experience': context.user_data['years_experience'],
        'goal': context.user_data['goal'],
    }

    save_user_to_db(user_data)

    # Получаем сохраненные данные для отображения даты
    saved_user = get_user_by_id(user.id)

    # Создаем клавиатуру с кнопками
    keyboard = [
        [KeyboardButton("/show_me"), KeyboardButton("/my_forms")],
        [KeyboardButton("/form"), KeyboardButton("/show_all")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

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

    # Очищаем временные данные
    context.user_data.clear()
    return ConversationHandler.END


# Команда отмены
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Заполнение анкеты отменено.")
    context.user_data.clear()
    return ConversationHandler.END


# Показать последнюю анкету текущего пользователя
async def show_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_data = get_user_by_id(user.id)

    if user_data:
        # Рассчитываем ИМТ (weight[4] / (height[3] в метрах)^2)
        bmi = user_data[4] / ((user_data[3] / 100) ** 2)

        await update.message.reply_text(
            "📋 Ваша последняя анкета:\n\n"
            f"📅 Дата заполнения: {user_data[8]}\n"
            f"✏️ Дата обновления: {user_data[9]}\n"
            f"📏 Рост: {user_data[3]} см\n"
            f"⚖️ Вес: {user_data[4]} кг\n"
            f"📊 ИМТ: {bmi:.1f}\n"
            f"🏃 Уровень активности: {user_data[5]}\n"
            f"👤 Пол: {user_data[6]}\n"
            f"🎂 Возраст: {user_data[7]} лет\n\n"
            "Чтобы увидеть все ваши анкеты, используйте /my_forms"
        )
    else:
        await update.message.reply_text(
            "❌ У вас еще нет заполненных анкет.\n"
            "Заполните анкету с помощью команды /form"
        )


# Показать все анкеты пользователя
async def show_my_forms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    forms = get_all_user_forms(user.id)

    if not forms:
        await update.message.reply_text(
            "❌ У вас еще нет заполненных анкет.\n"
            "Заполните анкету с помощью команды /form"
        )
        return

    response = f"📊 Все ваши анкеты ({len(forms)}):\n\n"

    for i, form in enumerate(forms, 1):
        height_cm = float(form[3])
        weight_kg = float(form[4])
        bmi = weight_kg / ((height_cm / 100) ** 2)
        response += (
                f"📋 Анкета #{i}:\n"
                f"  📅 Дата: {form[8]}\n"
                f"  📏 Рост: {form[3]} см\n"
                f"  ⚖️ Вес: {form[4]} кг\n"
                f"  📊 ИМТ: {bmi:.1f}\n"
                f"  🏃 Активность: {form[5]}\n"
                f"  👤 Пол: {form[6]}\n"
                f"  🎂 Возраст: {form[7]} лет\n"
                "─" * 30 + "\n"
        )

    # Разбиваем сообщение если оно слишком длинное
    if len(response) > 4096:
        for x in range(0, len(response), 4096):
            await update.message.reply_text(response[x:x + 4096])
    else:
        await update.message.reply_text(response)


# Показать все анкеты (последние от каждого пользователя)
async def show_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()

    if not users:
        await update.message.reply_text("❌ В базе данных пока нет анкет.")
        return

    response = f"📊 Все анкеты пользователей ({len(users)}):\n\n"

    for user in users:
        height_cm = float(user[3])
        weight_kg = float(user[4])
        bmi = weight_kg / ((height_cm / 100) ** 2)
        response += (
                f"👤 Пользователь ID: {user[1]}\n"
                f"  📅 Дата: {user[8]}\n"
                f"  📏 Рост: {user[3]} см\n"
                f"  ⚖️ Вес: {user[4]} кг\n"
                f"  📊 ИМТ: {bmi:.1f}\n"
                f"  🏃 Активность: {user[5]}\n"
                f"  👤 Пол: {user[6]}\n"
                f"  🎂 Возраст: {user[7]} лет\n"
                "─" * 30 + "\n"
        )

    # Разбиваем сообщение если оно слишком длинное
    if len(response) > 4096:
        for x in range(0, len(response), 4096):
            await update.message.reply_text(response[x:x + 4096])
    else:
        await update.message.reply_text(response)


# Обработчик текстовых сообщений для команды show
async def handle_show_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if text.startswith('show all') or text == 'all':
        await show_all(update, context)
    elif text.startswith('show me') or 'моя' in text:
        await show_me(update, context)
    elif 'мои анкеты' in text or 'my forms' in text:
        await show_my_forms(update, context)
    else:
        await update.message.reply_text(
            "Неизвестная команда. Используйте:\n"
            "/form - заполнить анкету\n"
            "/show_me - моя анкета\n"
            "/my_forms - все мои анкеты\n"
            "/show_all - все анкеты пользователей"
        )


# Основная функция
def main():
    # Инициализация базы данных
    init_db()

    # Создаем приложение
    application = Application.builder().token("8436312586:AAF7yu9aH20QJhCmj9yxJw54y-yvS9oOJqE").build()

    # Создаем ConversationHandler для анкеты
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('form', start_form)],
        states={
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_height)],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_weight)],
            ACTIVITY_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_activity_level)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            YEARS_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_years_experience)],
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_goal)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("show_me", show_me))
    application.add_handler(CommandHandler("show_all", show_all))
    application.add_handler(CommandHandler("my_forms", show_my_forms))
    application.add_handler(conv_handler)

    # Обработчик текстовых команд show
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_show_command))

    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()


if __name__ == '__main__':
    main()