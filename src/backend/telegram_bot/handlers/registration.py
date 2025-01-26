from telegram.ext import Application
from .reg_common import register_common_handlers
from .admin.reg_admin import register_admin_handlers
from .guest.reg_guest import register_guest_handlers
from .dispatcher.reg_dispatcher import register_dispatcher_handlers
from .executor.reg_executor import register_executor_handlers
from .specialist.reg_specialist import register_specialist_handlers
from .customer.reg_customer import register_customer_handlers
from .blocked.reg_blocked import register_blocked_handlers

def register_all_handlers(application: Application):
    """
    Централизованная регистрация всех обработчиков.
    """
    # Регистрируем общие обработчики
    register_common_handlers(application)

    # Регистрируем обработчики для каждой роли
    register_admin_handlers(application)
    register_guest_handlers(application)
    register_dispatcher_handlers(application)
    register_executor_handlers(application)
    register_specialist_handlers(application)
    register_customer_handlers(application)
    register_blocked_handlers(application)

    print("[INFO] Все обработчики успешно зарегистрированы.")
