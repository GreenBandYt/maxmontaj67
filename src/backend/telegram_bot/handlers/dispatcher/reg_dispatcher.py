from telegram.ext import Application, CommandHandler
from .dispatcher_menu import dispatcher_start

def register_dispatcher_handlers(application: Application):
    """
    Регистрирует обработчики для роли Диспетчер.
    """
    application.add_handler(CommandHandler("dispatcher", dispatcher_start))
