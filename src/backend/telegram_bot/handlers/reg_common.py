from telegram.ext import Application, CommandHandler
from handlers.common import start_command
from handlers.guest.guest_menu import (
    process_name,
    process_email,
    process_registration,
    handle_inline_buttons,
    handle_guest_help as help_command,
)

def register_common_handlers(application: Application):
    """
    Регистрирует обработчики для общих команд.
    """
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("name", process_name))
    application.add_handler(CommandHandler("email", process_email))
    application.add_handler(CommandHandler("register", process_registration))
