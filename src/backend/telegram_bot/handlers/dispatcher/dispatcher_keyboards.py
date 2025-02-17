from telegram import ReplyKeyboardMarkup

def dispatcher_menu_keyboard():
    """
    Возвращает клавиатуру для диспетчера.
    """
    return ReplyKeyboardMarkup(
        [
            ["📦 Текущие заказы", "📝 Создать заказ"],
            ["📅 Сегодня"], ["📞 Написать администратору"],
        ],
        resize_keyboard=True
    )
