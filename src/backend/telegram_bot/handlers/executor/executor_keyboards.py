# src/backend/telegram_bot/handlers/executor/executor_keyboards.py

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

def executor_montage_date_keyboard():
    """
    Возвращает клавиатуру для управления датой выполнения для исполнителя.
    """
    return ReplyKeyboardMarkup(
        [
            ["⬅️ Возврат в заказы"],
        ],
        resize_keyboard=True
    )

def executor_complete_order_keyboard():
    """
    Возвращает клавиатуру для завершения заказа для исполнителя.
    """
    return ReplyKeyboardMarkup(
        [
            ["📷 Добавить фото", "✅ Завершить"],
            ["🔙 Назад"]
        ],
        resize_keyboard=True
    )