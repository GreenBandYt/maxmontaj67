from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from .common import start_command, help_command, process_name, process_email, process_registration, handle_inline_buttons


def register_common_handlers(application: Application):
    """
    Регистрация общих обработчиков.
    """
    # Регистрируем команду /start
    application.add_handler(CommandHandler("start", start_command))

    # Добавляем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, process_registration))

    # Регистрируем обработчик нажатий Inline-кнопок
    application.add_handler(CallbackQueryHandler(handle_inline_buttons))


    # Регистрация команды /help
    application.add_handler(CommandHandler("help", help_command))

    # Регистрация обработчика кнопки "Помощь"
    application.add_handler(MessageHandler(filters.Text("🆘 Помощь"), help_command))
