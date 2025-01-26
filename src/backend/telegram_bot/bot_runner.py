import os
import sys
import logging
from handlers.registration import register_all_handlers
from bot_utils.bot_config import BOT_DB_CONFIG
from telegram.ext import ApplicationBuilder

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

def run_bot():
    """
    Запуск Telegram-бота.
    """
    try:
        # Проверяем наличие токена
        from bot_token import TELEGRAM_BOT_TOKEN
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("Токен Telegram не указан!")

        # Создаём приложение Telegram
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

        # Регистрируем обработчики
        register_all_handlers(application)

        logging.info("Telegram-бот успешно запущен. Ожидание сообщений...")
        application.run_polling()

    except Exception as e:
        logging.error(f"Ошибка запуска бота: {e}")

if __name__ == "__main__":
    run_bot()
