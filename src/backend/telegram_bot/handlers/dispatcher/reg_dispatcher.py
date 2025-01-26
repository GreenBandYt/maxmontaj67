from telegram.ext import Application, CommandHandler
from .dispatcher_menu import (
    dispatcher_start,
    handle_dispatcher_current_orders,
    handle_dispatcher_create_order,
    handle_dispatcher_today
)

def register_dispatcher_handlers(application: Application):
    """
    Регистрирует обработчики для роли Диспетчер.
    """
    application.add_handler(CommandHandler("dispatcher", dispatcher_start))
    application.add_handler(CommandHandler("dispatcher_current_orders", handle_dispatcher_current_orders))
    application.add_handler(CommandHandler("dispatcher_create_order", handle_dispatcher_create_order))
    application.add_handler(CommandHandler("dispatcher_today", handle_dispatcher_today))
