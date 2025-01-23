from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from .guest_menu import start_guest, handle_guest_action

def register_guest_handlers(application: Application):
    """
    Регистрирует обработчики для роли Гость.
    """
    # Обработчик команды /guest_start
    application.add_handler(CommandHandler("guest_start", start_guest))

    # Обработчик для действий с уникальным callback_data
    application.add_handler(CallbackQueryHandler(handle_guest_action, pattern="^guest_"))
