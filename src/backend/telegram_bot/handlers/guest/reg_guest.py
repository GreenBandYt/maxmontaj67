from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from .guest_menu import (
    start_guest,
    handle_guest_register,
)

def register_guest_handlers(application: Application):
    """
    Регистрирует обработчики для роли Гость.
    """
    application.add_handler(CommandHandler("guest_start", start_guest))
    application.add_handler(CommandHandler("guest_register", handle_guest_register))

