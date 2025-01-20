from telegram.ext import Application, CommandHandler, MessageHandler, filters
from .common import start_command, help_command


def register_common_handlers(application: Application):
    """
    Регистрация общих обработчиков.
    """
    # Регистрируем команду /start
    application.add_handler(CommandHandler("start", start_command))

    # Регистрация команды /help
    application.add_handler(CommandHandler("help", help_command))

    # Регистрация обработчика кнопки "Помощь"
    application.add_handler(MessageHandler(filters.Text("🆘 Помощь"), help_command))
    