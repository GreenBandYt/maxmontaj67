from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def start_guest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /guest_start. Приветствует гостя.
    """
    user_name = update.effective_user.first_name
    keyboard = [
        [InlineKeyboardButton("✍️ Регистрация", callback_data="guest_register")],
        [InlineKeyboardButton("🆘 Помощь", callback_data="guest_help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Добро пожаловать, {user_name}! 👋\n"
        "Вы находитесь в гостевой зоне. Зарегистрируйтесь, чтобы получить доступ к функционалу!",
        reply_markup=reply_markup
    )

async def handle_guest_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает действия гостя: Регистрация или Помощь.
    """
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие кнопки

    if query.data == "guest_register":
        await query.edit_message_text("Пожалуйста, введите ваше имя для начала регистрации.")
        context.user_data['step'] = 'registration_name'

    elif query.data == "guest_help":
        await query.edit_message_text("Гостевая помощь: Вы можете зарегистрироваться или обратиться к администратору.")
