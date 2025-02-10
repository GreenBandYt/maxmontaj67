from telegram import ReplyKeyboardMarkup

def blocked_keyboard():
    """
    Возвращает клавиатуру для заблокированного пользователя.
    """
    return ReplyKeyboardMarkup(
        [
            ["📞 Написать администратору"]
        ],
        resize_keyboard=True
    )
