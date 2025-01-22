from telegram import Update
from telegram.ext import ContextTypes
from .dispatcher_keyboards import dispatcher_keyboard

async def dispatcher_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Стартовая страница для диспетчера.
    """
    await update.message.reply_text(
        f"Добро пожаловать, {update.effective_user.first_name}!\n"
        "Вы вошли как Диспетчер.\n"
        "Что вы хотите сделать?",
        reply_markup=dispatcher_keyboard()  # Клавиатура для диспетчера
    )
