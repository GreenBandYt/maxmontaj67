import os
import sys
import logging
import inspect
from functools import wraps
from telegram_bot.handlers.registration import register_all_handlers
from bot_utils.bot_config import BOT_DB_CONFIG
from telegram.ext import ApplicationBuilder

# Добавляем папку "telegram_bot" в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# def find_decorated_functions():
#     """
#     Поиск всех функций, которые имеют декораторы.
#     """
#     decorated_functions = []
#
#     logging.info("Поиск задекорированных функций...")
#
#     for name, func in globals().items():
#         if callable(func) and hasattr(func, '__wrapped__'):
#             logging.info(f"Найдена задекорированная функция: {func.__name__}")
#             decorated_functions.append({
#                 "function_name": func.__name__,
#                 "decorator": func.__wrapped__.__name__,
#                 "module": func.__module__,
#                 "description": func.__doc__ or "Описание отсутствует"
#             })
#
#     logging.info(f"Найдено декорированных функций: {len(decorated_functions)}")
#     return decorated_functions


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
