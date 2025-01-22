from telegram import ReplyKeyboardMarkup

def specialist_keyboard():
    """
    Возвращает клавиатуру для специалиста.
    """
    return ReplyKeyboardMarkup(
        [
            ["📋 Новые задания", "🗂️ Текущие задания"],
            ["✉️ Связаться"]
        ],
        resize_keyboard=True
    )
