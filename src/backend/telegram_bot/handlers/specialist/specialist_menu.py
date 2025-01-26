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

async def handle_specialist_new_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка кнопки "📋 Новые задания".
    """
    await update.message.reply_text("Показать новые задания для специалиста.")

async def handle_specialist_current_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка кнопки "🗂️ Текущие задания".
    """
    await update.message.reply_text("Показать текущие задания для специалиста.")

async def handle_specialist_contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка кнопки "✉️ Связаться".
    """
    await update.message.reply_text("Свяжитесь с администратором, чтобы решить вашу проблему.")
