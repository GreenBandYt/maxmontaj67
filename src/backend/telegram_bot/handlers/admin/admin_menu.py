from telegram import Update
from telegram.ext import ContextTypes
from .admin_keyboards import admin_menu_keyboard

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Стартовая страница для администратора.
    """
    await update.message.reply_text(
        f"Добро пожаловать, {update.effective_user.first_name}!\n"
        "Вы вошли как Администратор.\n"
        "Выберите действие из меню ниже:",
        reply_markup=admin_menu_keyboard()
    )
