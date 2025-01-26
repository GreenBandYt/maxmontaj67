from telegram.ext import Application, CommandHandler
from .admin_menu import admin_start

def register_admin_handlers(application: Application):
    """
    Регистрирует обработчики для роли Администратор.
    """
    # Регистрация команды /admin для отображения главного меню
    application.add_handler(CommandHandler("admin", admin_start))
