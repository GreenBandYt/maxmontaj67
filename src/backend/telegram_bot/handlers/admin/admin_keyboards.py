from telegram import ReplyKeyboardMarkup

def admin_menu_keyboard():
    """
    Возвращает клавиатуру для администратора.
    """
    return ReplyKeyboardMarkup(
        [
            ["📊 Аналитика", "👥 Пользователи"],
            ["📂 Заказы", "🔔 Уведомление"]
        ],
        resize_keyboard=True
    )
