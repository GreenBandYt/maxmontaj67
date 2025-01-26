from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from handlers.common import start_command,  handle_user_input
from handlers.common import handle_inline_buttons

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

    print("[INFO] Общие обработчики успешно зарегистрированы.")
