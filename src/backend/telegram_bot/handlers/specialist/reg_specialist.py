from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from .specialist_menu import (
    specialist_start,
    handle_specialist_new_tasks,
    handle_specialist_current_tasks,

    handle_specialist_accept_order,
    handle_specialist_decline_order,
)

def register_specialist_handlers(application: Application):
    """
    Регистрирует обработчики для роли Специалист.
    """
    # Обработчик команды /executor
    application.add_handler(CommandHandler("specialist", specialist_start))

    # Регистрируем действия из меню
    application.add_handler(CommandHandler("specialist_new_tasks", handle_specialist_new_tasks))
    application.add_handler(CommandHandler("specialist_current_tasks", handle_specialist_current_tasks))
    # application.add_handler(CommandHandler("specialist_contact_admin", handle_specialist_contact_admin))

    # Регистрируем ин-лайн кнопки
    application.add_handler(CallbackQueryHandler(handle_specialist_accept_order, pattern="^specialist_accept_order_"))
    application.add_handler(CallbackQueryHandler(handle_specialist_decline_order, pattern="^specialist_decline_order_"))

