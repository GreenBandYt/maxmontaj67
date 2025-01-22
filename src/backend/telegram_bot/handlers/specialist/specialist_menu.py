from telegram import Update
from telegram.ext import ContextTypes
from .specialist_keyboards import specialist_keyboard

async def specialist_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Стартовая страница для специалиста.
    """
    await update.message.reply_text(
        f"Добро пожаловать, {update.effective_user.first_name}!\n"
        "Вы вошли как Специалист.\n"
        "Что вы хотите сделать?",
        reply_markup=specialist_keyboard()  # Клавиатура для специалиста
    )
