import logging
from telegram.ext import Application
from telegram_bot.handlers.reg_common import register_common_handlers
from telegram_bot.handlers.admin.reg_admin import register_admin_handlers
from telegram_bot.handlers.guest.reg_guest import register_guest_handlers
from telegram_bot.handlers.dispatcher.reg_dispatcher import register_dispatcher_handlers
from telegram_bot.handlers.executor.reg_executor import register_executor_handlers
from telegram_bot.handlers.specialist.reg_specialist import register_specialist_handlers
from telegram_bot.handlers.customer.reg_customer import register_customer_handlers
from telegram_bot.handlers.blocked.reg_blocked import register_blocked_handlers

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

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

    logger.info("Все обработчики успешно зарегистрированы.")
