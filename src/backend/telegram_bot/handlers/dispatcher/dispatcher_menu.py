from telegram import Update
from telegram.ext import ContextTypes
from .dispatcher_keyboards import dispatcher_menu_keyboard

async def dispatcher_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Стартовая страница для диспетчера.
    """
    await update.message.reply_text(
        f"Добро пожаловать, {update.effective_user.first_name}!\n"
        "Вы вошли как Диспетчер. Выберите действие из меню ниже:",
        reply_markup=dispatcher_menu_keyboard()
    )

async def handle_dispatcher_current_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка кнопки "📦 Текущие заказы".
    """
    await update.message.reply_text("Здесь список ваших текущих заказов. 📦")

async def handle_dispatcher_create_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка кнопки "📝 Создать заказ".
    """
    await update.message.reply_text("Процесс создания заказа начат. 📝 Введите данные заказа.")

async def handle_dispatcher_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка кнопки "📅 Сегодня".
    """
    await update.message.reply_text("Вот список задач на сегодня. 📅")
