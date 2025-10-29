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
    [KeyboardButton("⏭️ Скип дня"), KeyboardButton("📊 Статус")],
    [KeyboardButton("⏸️ Пропустить день (тест)"), KeyboardButton("⬅️ Предыдущая неделя")],
    [KeyboardButton("➡️ Следующая неделя"), KeyboardButton("🏠 Главное меню")]
]