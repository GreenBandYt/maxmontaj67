from telegram import ReplyKeyboardMarkup

def blocked_keyboard():
    """
    Возвращает клавиатуру для заблокированного пользователя.
    """
    return ReplyKeyboardMarkup(
        [
            ["📞 Связаться с администратором"]
        ],
        resize_keyboard=True
    )
