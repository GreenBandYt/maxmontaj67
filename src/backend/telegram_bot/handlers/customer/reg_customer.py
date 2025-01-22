from telegram.ext import Application, CommandHandler
from .customer_menu import customer_start

def register_customer_handlers(application: Application):
    """
    Регистрирует обработчики для роли Заказчик.
    """
    application.add_handler(CommandHandler("customer", customer_start))

