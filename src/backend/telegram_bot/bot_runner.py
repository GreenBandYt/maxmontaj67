import os
import sys
import logging
import asyncio
import threading
import signal  # ✅ Для корректного завершения
from telegram.ext import ApplicationBuilder
from telegram_bot.handlers.registration import register_all_handlers
from bot_utils.bot_config import BOT_DB_CONFIG

# ✅ Добавляем корневую папку в `sys.path`
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ✅ Логирование путей
logging.info(f"🔍 sys.path в bot_runner.py:\n" + "\n".join(sys.path))

# ✅ Переменная для управления потоком `start_notifications`
notification_thread = None
stop_notifications = threading.Event()  # Флаг для остановки

def start_notifications():
    """Фоновый запуск `notifications.py`"""
    global stop_notifications

    import os
    import sys
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)

    from bot_utils.messages.notifications import send_notifications

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        while not stop_notifications.is_set():
            loop.run_until_complete(send_notifications())
    except Exception as e:
        logging.error(f"❌ Ошибка в потоке `start_notifications`: {e}")

def stop_all():
    """🛑 Останавливает `start_notifications` и Telegram-бот перед выходом."""
    global notification_thread, stop_notifications

    logging.info("🛑 Остановка всех фоновых процессов...")

    # ✅ Останавливаем поток `start_notifications`
    if notification_thread and notification_thread.is_alive():
        stop_notifications.set()
        notification_thread.join()

    logging.info("✅ Все фоновые процессы остановлены.")

def run_bot():
    """
    Запуск Telegram-бота и системы уведомлений.
    """
    global notification_thread, stop_notifications

    try:
        from bot_token import TELEGRAM_BOT_TOKEN
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("Токен Telegram не указан!")

        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        register_all_handlers(application)

        # ✅ Запускаем `notifications.py` в отдельном потоке (если не запущен)
        if not notification_thread or not notification_thread.is_alive():
            stop_notifications.clear()
            notification_thread = threading.Thread(target=start_notifications, daemon=True)
            notification_thread.start()
            logging.info("📢 Уведомления о заказах запущены в фоновом режиме!")

        logging.info("✅ Telegram-бот успешно запущен. Ожидание сообщений...")
        application.run_polling()

    except Exception as e:
        logging.error(f"❌ Ошибка запуска бота: {e}")

if __name__ == "__main__":
    # ✅ Обработчик выхода, чтобы останавливать `start_notifications`
    signal.signal(signal.SIGINT, lambda signum, frame: stop_all())
    signal.signal(signal.SIGTERM, lambda signum, frame: stop_all())

    run_bot()
