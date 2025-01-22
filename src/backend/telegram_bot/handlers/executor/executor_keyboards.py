from telegram import ReplyKeyboardMarkup

def executor_keyboard():
    """
    Возвращает клавиатуру для исполнителя.
    """
    return ReplyKeyboardMarkup(
        [
            ["📋 Новые задания", "🗂️ Текущие задания"],
            ["✉️ Связаться"]
        ],
        resize_keyboard=True
    )
