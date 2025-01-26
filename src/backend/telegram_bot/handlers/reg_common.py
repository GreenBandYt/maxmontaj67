from telegram.ext import Application, CommandHandler, MessageHandler, filters
from handlers.common import start_command, help_command, handle_user_input

def register_common_handlers(application: Application):
    """
    Регистрирует обработчики для общих команд.
    """
    # Обработка команды /start
    application.add_handler(CommandHandler("start", start_command))

    # Обработка команды /help (общая логика для всех ролей)
    application.add_handler(CommandHandler("help", help_command))

    # Универсальный обработчик для текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))

    print("[INFO] Общие обработчики успешно зарегистрированы.")
