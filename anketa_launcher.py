from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, filters
from handlers.show import show_me, show_my_forms, show_all, handle_show_command, clear_last, clear_all
from handlers.form import cancel

from utils.states import HEIGHT, WEIGHT, ACTIVITY_LEVEL, GENDER, YEARS_EXPERIENCE, GOAL
from handlers.form import start_form, get_height, get_weight, get_activity_level, get_gender, get_years_experience, get_goal


def create_anketa_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler('form', start_form)],
        states={
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_height)],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_weight)],
            ACTIVITY_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_activity_level)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            YEARS_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_years_experience)],
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_goal)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )


def register_anketa_handlers(application):
    application.add_handler(CommandHandler("show_me", show_me))
    application.add_handler(CommandHandler("show_all", show_all))
    application.add_handler(CommandHandler("my_forms", show_my_forms))
    application.add_handler(CommandHandler("clear_last", clear_last))
    application.add_handler(CommandHandler("clear_all", clear_all))
    application.add_handler(create_anketa_conversation())
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_show_command))


