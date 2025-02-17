from telegram import ReplyKeyboardMarkup

def customer_keyboard():
    """
    Возвращает клавиатуру для заказчика.
    """
    return ReplyKeyboardMarkup(
        [
            ["🛒 Сделать заказ", "📃 Мои заказы"],
            ["📞 Написать администратору"]
        ],
        resize_keyboard=True
    )

