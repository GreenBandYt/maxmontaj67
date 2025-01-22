from telegram.ext import Application, CommandHandler
from .admin_menu import admin_start

def register_admin_handlers(application: Application):
    """
    Регистрирует обработчики для роли Администратор.
    """
    application.add_handler(CommandHandler("admin", admin_start))
