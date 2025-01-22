from telegram import ReplyKeyboardMarkup

def customer_keyboard():
    """
    Возвращает клавиатуру для заказчика.
    """
    return ReplyKeyboardMarkup(
        [
            ["🛒 Сделать заказ", "📃 Мои заказы"],
            ["💬 Написать"]
        ],
        resize_keyboard=True
    )
