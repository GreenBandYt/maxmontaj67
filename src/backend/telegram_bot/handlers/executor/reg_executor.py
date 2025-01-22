from telegram.ext import Application, CommandHandler
from .executor_menu import executor_start

def register_executor_handlers(application: Application):
    """
    Регистрирует обработчики для роли Исполнитель.
    """
    application.add_handler(CommandHandler("executor", executor_start))
