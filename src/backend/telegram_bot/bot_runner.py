from telegram.ext import ApplicationBuilder
from handlers.registration import register_all_handlers

# Импорт токена из локального файла token.py
try:
    from bot_token import TELEGRAM_BOT_TOKEN
except ImportError:
    raise ImportError("Токен не найден! Убедитесь, что он находится в файле token.py внутри src/backend/telegram_bot.")

def run_bot():
    """
    Запуск Telegram-бота.
    """
    # Проверка наличия токена
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("Токен Telegram не указан!")

    # Создание приложения Telegram
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрация всех обработчиков через registration.py
    register_all_handlers(application)

    print("Telegram-бот запущен. Ожидание сообщений...")
    application.run_polling()

if __name__ == "__main__":
    run_bot()
