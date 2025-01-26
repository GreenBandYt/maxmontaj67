from telegram.ext import Application, CommandHandler
from .blocked_menu import (
    blocked_start,
    handle_blocked_contact_admin,
)

def register_blocked_handlers(application: Application):
    """
    Регистрирует обработчики для роли Заблокированный.
    """
    application.add_handler(CommandHandler("blocked", blocked_start))
    application.add_handler(CommandHandler("blocked_contact_admin", handle_blocked_contact_admin))
