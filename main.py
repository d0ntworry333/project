import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes

from database.DataBase import init_db, get_user_by_id
from anketa_launcher import register_anketa_handlers


# Логирование  
logging.basicConfig(
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
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
    keyboard = [
        [KeyboardButton("/show_me"), KeyboardButton("/my_forms")],
        [KeyboardButton("/form"), KeyboardButton("/show_all")],
        [KeyboardButton("/clear_last"), KeyboardButton("/clear_all")],
        [KeyboardButton("/cancel")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)


def main():
    init_db()
    application = Application.builder().token("8436312586:AAF7yu9aH20QJhCmj9yxJw54y-yvS9oOJqE").build()
    application.add_handler(CommandHandler("start", start))
    register_anketa_handlers(application)
    print("Бот запущен...")
    application.run_polling()


if __name__ == '__main__':
    main()
