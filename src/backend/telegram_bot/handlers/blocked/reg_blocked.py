from telegram.ext import Application, CommandHandler
from .blocked_menu import blocked_start

def register_blocked_handlers(application: Application):
    """
    Регистрирует обработчики для роли Заблокированный.
    """
    application.add_handler(CommandHandler("blocked", blocked_start))
