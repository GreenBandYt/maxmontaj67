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
        "Выберите действие из меню ниже:",
        reply_markup=executor_keyboard()  # Клавиатура для исполнителя
    )

async def handle_executor_new_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Здесь отображаются новые задания.")

async def handle_executor_current_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Вот список ваших текущих заданий.")

async def handle_executor_contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Вы можете написать администратору прямо здесь.")
