from telebot.types import KeyboardButton

menu_keyboard = [
            [KeyboardButton("/main"), KeyboardButton("/achievements")]
    ]


main_keyboard = [
    [KeyboardButton("/questionnaire"), KeyboardButton("/will be decided")],
    [KeyboardButton("/recovery recommendations"), KeyboardButton("/training process")]
]

anketa_keyboard = [
    [KeyboardButton("/form"), KeyboardButton("/return")],
    [KeyboardButton("/clear_last"), KeyboardButton("/show_all")],
    [KeyboardButton("/cancel"), KeyboardButton("/clear_all")]
]