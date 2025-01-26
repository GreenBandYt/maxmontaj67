from telegram import ReplyKeyboardMarkup

def executor_keyboard():
    """
    Возвращает клавиатуру для исполнителя.
    """
    return ReplyKeyboardMarkup(
        [
            ["📋 Новые задания", "🔄 Задания в работе"],
            ["📞 Написать администратору"]
        ],
        resize_keyboard=True
    )
