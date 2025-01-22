from telegram import Update
from telegram.ext import ContextTypes
from .customer_keyboards import customer_keyboard

async def customer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Стартовая страница для заказчика.
    """
    await update.message.reply_text(
        f"Добро пожаловать, {update.effective_user.first_name}!\n"
        "Вы вошли как Заказчик.\n"
        "Что вы хотите сделать?",
        reply_markup=customer_keyboard()  # Клавиатура для заказчика
    )

