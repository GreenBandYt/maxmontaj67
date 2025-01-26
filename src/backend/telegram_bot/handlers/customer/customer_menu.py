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

async def handle_customer_make_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка кнопки "🛒 Сделать заказ".
    """
    await update.message.reply_text("Давайте начнём оформлять ваш заказ. 🛒\nПожалуйста, выберите категорию товаров.")

async def handle_customer_my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка кнопки "📃 Мои заказы".
    """
    await update.message.reply_text("Вот список ваших текущих заказов. 📃\nВыберите заказ для подробной информации.")

async def handle_customer_contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка кнопки "💬 Написать".
    """
    await update.message.reply_text("Вы можете задать вопрос администратору. 💬\nНапишите своё сообщение, и мы передадим его.")
