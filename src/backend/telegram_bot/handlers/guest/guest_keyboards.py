from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def guest_keyboard():
    """
    Возвращает клавиатуру для гостей.
    """
    return ReplyKeyboardMarkup(
        [["✍️ Регистрация", "🆘 Помощь"], ["📞 Написать администратору"]],
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
