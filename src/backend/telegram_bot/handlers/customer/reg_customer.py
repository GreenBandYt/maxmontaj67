from telegram.ext import Application, CommandHandler
from .customer_menu import (
    customer_start,
    handle_customer_make_order,
    handle_customer_my_orders,
    handle_customer_contact_admin,
)

def register_customer_handlers(application: Application):
    """
    Регистрирует обработчики для роли Заказчик.
    """
    application.add_handler(CommandHandler("customer", customer_start))
    application.add_handler(CommandHandler("customer_make_order", handle_customer_make_order))
    application.add_handler(CommandHandler("customer_my_orders", handle_customer_my_orders))
    application.add_handler(CommandHandler("customer_contact_admin", handle_customer_contact_admin))
