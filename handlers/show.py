from telegram import Update
from telegram.ext import ContextTypes

from database.DataBase import get_user_by_id, get_all_user_forms, get_all_users, delete_last_user_form, delete_all_user_forms
from error_solutions import send_long_message


async def show_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_data = get_user_by_id(user.id)
    if user_data:
        bmi = float(user_data[4]) / ((float(user_data[3]) / 100) ** 2)
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
    await send_long_message(update.message.reply_text, response)


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
    await send_long_message(update.message.reply_text, response)


async def handle_show_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text.startswith('show all') or text == 'all':
        await show_all(update, context)
    elif text.startswith('show me') or 'моя' in text:
        await show_me(update, context)
    elif 'мои анкеты' in text or 'my forms' in text:
        await show_my_forms(update, context)
    else:
        await send_long_message(update.message.reply_text,
                                "Неизвестная команда. Используйте:\n"
                                "/form - заполнить анкету\n"
                                "/show_me - моя анкета\n"
                                "/my_forms - все мои анкеты\n"
                                "/show_all - все анкеты пользователей\n"
                                "/clear_last - удалить мою последнюю анкету\n"
                                "/clear_all - удалить все мои анкеты")


async def clear_last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    deleted = delete_last_user_form(user.id)
    if deleted:
        await update.message.reply_text("Последняя анкета удалена.")
    else:
        await update.message.reply_text("Удалять нечего — анкет не найдено.")


async def clear_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    deleted = delete_all_user_forms(user.id)
    if deleted:
        await update.message.reply_text("Все ваши анкеты удалены.")
    else:
        await update.message.reply_text("Удалять нечего — анкет не найдено.")


