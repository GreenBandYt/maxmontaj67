from telegram.ext import Application, CommandHandler
from .specialist_menu import specialist_start

def register_specialist_handlers(application: Application):
    """
    Регистрирует обработчики для роли Специалист.
    """
    application.add_handler(CommandHandler("specialist", specialist_start))

