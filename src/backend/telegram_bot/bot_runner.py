import os
import sys
import logging
import asyncio
import threading  # ✅ Добавляем потоки
from telegram.ext import ApplicationBuilder
from telegram_bot.handlers.registration import register_all_handlers
from bot_utils.bot_config import BOT_DB_CONFIG

# Добавляем папку "telegram_bot" в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# ✅ Функция для запуска `notifications.py` в отдельном потоке
def start_notifications():
    from bot_utils.messages.notifications import send_notifications  # ✅ Импорт функции отправки уведомлений
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_notifications())


def run_bot():
    """
    Запуск Telegram-бота и системы уведомлений.
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

        # ✅ Запускаем `notifications.py` в отдельном потоке
        notification_thread = threading.Thread(target=start_notifications, daemon=True)
        notification_thread.start()
        logging.info("📢 Уведомления о заказах запущены в фоновом режиме!")

        logging.info("✅ Telegram-бот успешно запущен. Ожидание сообщений...")
        application.run_polling()

    except Exception as e:
        logging.error(f"❌ Ошибка запуска бота: {e}")


if __name__ == "__main__":
    run_bot()
