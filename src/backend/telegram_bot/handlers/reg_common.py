import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram_bot.handlers.common import start_command, handle_user_input, handle_inline_buttons

# Настройка логирования
logger = logging.getLogger(__name__)

def register_common_handlers(application: Application):
    """
    Регистрирует обработчики для общих команд.
    """
    # Обработка команды /start
    application.add_handler(CommandHandler("start", start_command))

    # Универсальный обработчик для текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))

    # Регистрируем обработчик инлайн-кнопок
    application.add_handler(CallbackQueryHandler(handle_inline_buttons))

    logger.info("Общие обработчики успешно зарегистрированы.")
