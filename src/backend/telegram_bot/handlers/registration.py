from telegram.ext import Application
from .reg_common import register_common_handlers
from .admin.reg_admin import register_admin_handlers

def register_all_handlers(application: Application):
    """
    Централизованная регистрация всех обработчиков.
    """
    # Регистрируем общие обработчики
    register_common_handlers(application)

    # Регистрируем обработчики для администратора
    register_admin_handlers(application)
