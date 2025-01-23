from telegram import ReplyKeyboardMarkup

def guest_keyboard():
    """
    Возвращает клавиатуру для гостей.
    """
    return ReplyKeyboardMarkup(
        [["✍️ Регистрация", "🆘 Помощь"]],
        resize_keyboard=True
    )
