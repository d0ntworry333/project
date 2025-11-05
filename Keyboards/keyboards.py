from telegram import Update, ReplyKeyboardMarkup, KeyboardButton

menu_keyboard = [
    [KeyboardButton("main"), KeyboardButton("/achievements")]
]

main_keyboard = [
    [KeyboardButton("questionnaire"), KeyboardButton("goal & diet")],
    [KeyboardButton("recovery recommendations"), KeyboardButton("training process")],
    [KeyboardButton("main menu")]
]

anketa_keyboard = [
    [KeyboardButton("/form"), KeyboardButton("return")],
    [KeyboardButton("/clear_last"), KeyboardButton("/show_all")],
    [KeyboardButton("/cancel"), KeyboardButton("/clear_all")]
]

training_keyboard = [
    [KeyboardButton("📋 Упражнения дня"), KeyboardButton("📅 Расписание")],
    [KeyboardButton("✅ Я выполнил тренировку"), KeyboardButton("📊 Статус")],
    [KeyboardButton("🧠 Техника"), KeyboardButton("🏠 Главное меню")],
    [KeyboardButton("⬅️ Предыдущая неделя"), KeyboardButton("➡️ Следующая неделя")]
]


technique_keyboard = [
    [KeyboardButton("руки"), KeyboardButton("спина")],
    [KeyboardButton("ноги"), KeyboardButton("return")]
]