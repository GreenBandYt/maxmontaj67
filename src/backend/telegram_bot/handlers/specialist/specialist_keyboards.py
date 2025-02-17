# src/backend/telegram_bot/handlers/specialist/specialist_keyboards.py

from telegram import ReplyKeyboardMarkup

def specialist_keyboard():
    """
    Возвращает клавиатуру для специалиста.
    """
    return ReplyKeyboardMarkup(
        [
            ["📋 Список новых заданий", "🔄 Текущие задания"],
            ["📞 Написать администратору"]
        ],
        resize_keyboard=True
    )

def specialist_montage_date_keyboard():
    """
    Возвращает клавиатуру для управления датой монтажа для специалиста.
    """
    return ReplyKeyboardMarkup(
        [
            ["⬅️ Возврат в меню"],
        ],
        resize_keyboard=True
    )


def specialist_complete_order_keyboard():
    """
    Возвращает клавиатуру для завершения заказа для специалиста.
    """
    return ReplyKeyboardMarkup(
        [
            ["📷 Добавить фото", "✅ Завершить"],
            ["⬅️ Возврат в меню"]
        ],
        resize_keyboard=True
    )