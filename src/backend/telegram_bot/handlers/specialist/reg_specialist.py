from telegram.ext import Application, CommandHandler
from .specialist_menu import (
    specialist_start,
    handle_specialist_new_tasks,
    handle_specialist_current_tasks,
    handle_specialist_contact_admin,
)

def register_specialist_handlers(application: Application):
    """
    Регистрирует обработчики для роли Специалист.
    """
    application.add_handler(CommandHandler("specialist", specialist_start))
    application.add_handler(CommandHandler("specialist_new_tasks", handle_specialist_new_tasks))
    application.add_handler(CommandHandler("specialist_current_tasks", handle_specialist_current_tasks))
    application.add_handler(CommandHandler("specialist_contact_admin", handle_specialist_contact_admin))
