from telegram import Update
from telegram.ext import ContextTypes
from .executor_keyboards import executor_keyboard

async def executor_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Стартовая страница для исполнителя.
    """
    await update.message.reply_text(
        f"Добро пожаловать, {update.effective_user.first_name}!\n"
        "Вы вошли как Исполнитель.\n"
        "Что вы хотите сделать?",
        reply_markup=executor_keyboard()  # Клавиатура для исполнителя
    )
