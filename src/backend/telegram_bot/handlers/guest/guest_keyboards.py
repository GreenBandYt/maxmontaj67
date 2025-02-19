# src/backend/telegram_bot/handlers/guest/guest_keyboards.py

from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def guest_keyboard():
    """
    Возвращает клавиатуру для гостей.
    """
    return ReplyKeyboardMarkup(
        [["✍️ Регистрация"], ["📞 Написать администратору"]],
        resize_keyboard=True
    )

def generate_email_error_keyboard():
    """
    Возвращает Inline-клавиатуру для выбора действий при неверном email.
    """
    keyboard = [
        [InlineKeyboardButton("🔁 Повторить ввод имени", callback_data="repeat_name")],
        [InlineKeyboardButton("✍️ Зарегистрироваться", callback_data="register_user")],
        [InlineKeyboardButton("📞 Написать администратору", callback_data="contact_admin")],
    ]
    return InlineKeyboardMarkup(keyboard)

def generate_admin_message_keyboard():
    """
    Возвращает Inline-клавиатуру с кнопкой '⬅️ Вернуться к выбору действия'.
    """
    keyboard = [
        [InlineKeyboardButton("⬅️ Вернуться к выбору действия", callback_data="return_to_action")],
    ]
    return InlineKeyboardMarkup(keyboard)

def generate_role_selection_keyboard():
    """
    Возвращает Inline-клавиатуру для выбора роли при регистрации.
    """
    keyboard = [
        [InlineKeyboardButton("👷 Исполнитель", callback_data="register_role_executor")],
        [InlineKeyboardButton("🔧 Специалист (временно недоступно)", callback_data="")],  # Оставляем callback_data пустым
        [InlineKeyboardButton("🛒 Заказчик (временно недоступно)", callback_data="")],  # Оставляем callback_data пустым
        [InlineKeyboardButton("⬅️ Назад", callback_data="register_role_back")],
    ]
    return InlineKeyboardMarkup(keyboard)

