from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from .executor_menu import (
    executor_start, handle_executor_new_tasks, handle_executor_current_tasks, handle_executor_contact_admin,
    handle_executor_accept_order,handle_executor_decline_order,

)

def register_executor_handlers(application: Application):
    """
    Регистрирует обработчики для роли Исполнитель.
    """
    # Обработчик команды /executor
    application.add_handler(CommandHandler("executor", executor_start))

    # Регистрируем действия из меню
    application.add_handler(CommandHandler("executor_new_tasks", handle_executor_new_tasks))
    application.add_handler(CommandHandler("executor_current_tasks", handle_executor_current_tasks))
    application.add_handler(CommandHandler("executor_contact_admin", handle_executor_contact_admin))

    # Регистрируем ин-лайн кнопки
    application.add_handler(CallbackQueryHandler(handle_executor_accept_order, pattern="^executor_accept_order_"))
    application.add_handler(CallbackQueryHandler(handle_executor_decline_order, pattern="^executor_decline_order_"))

