from telegram import Update
from telegram.ext import ContextTypes
from .blocked_keyboards import blocked_keyboard

async def blocked_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Стартовая страница для заблокированного пользователя.
    """
    await update.message.reply_text(
        f"Вы заблокированы в системе, {update.effective_user.first_name}.\n"
        "Свяжитесь с администратором для уточнения.",
        reply_markup=blocked_keyboard()  # Клавиатура для заблокированного пользователя
    )
