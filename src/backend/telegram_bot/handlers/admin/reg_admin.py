from telegram.ext import Application, CommandHandler
from .admin_menu import (
    admin_start,
    handle_admin_analytics,
    handle_admin_users,
    handle_admin_orders,
    handle_admin_notifications,
)

def register_admin_handlers(application: Application):
    """
    Регистрирует обработчики для роли Администратор.
    """
    application.add_handler(CommandHandler("admin", admin_start))
    application.add_handler(CommandHandler("admin_analytics", handle_admin_analytics))
    application.add_handler(CommandHandler("admin_users", handle_admin_users))
    application.add_handler(CommandHandler("admin_orders", handle_admin_orders))
    application.add_handler(CommandHandler("admin_notifications", handle_admin_notifications))
