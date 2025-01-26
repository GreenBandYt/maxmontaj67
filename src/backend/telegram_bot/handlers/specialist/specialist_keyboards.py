from telegram import ReplyKeyboardMarkup

def specialist_keyboard():
    """
    Возвращает клавиатуру для специалиста.
    """
    return ReplyKeyboardMarkup(
        [
            ["📋 Список новых заданий", "🔄 Текущие задания"],
            ["📞 Связаться с администратором"]
        ],
        resize_keyboard=True
    )
