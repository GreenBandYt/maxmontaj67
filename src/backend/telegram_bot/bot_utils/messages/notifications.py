import os
import sys
import logging
import asyncio
import pymysql
import pytz

from datetime import datetime, timedelta
from telegram import Bot
from telegram_bot.bot_token import TELEGRAM_BOT_TOKEN

# ✅ Добавляем корневую папку "src" в `sys.path`
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ✅ Импорт `db_connect`
from telegram_bot.bot_utils.bot_db_utils import db_connect

# 🛠 Настройка логирования
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# 📢 Инициализация бота
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# 🌍 Устанавливаем московский часовой пояс
MOSCOW_TZ = pytz.timezone("Europe/Moscow")


async def send_notifications():
    """🔄 Запускает процесс проверки и отправки новых уведомлений."""
    while True:
        now = datetime.now(MOSCOW_TZ)
        work_hours_start, work_hours_end, repeat_interval, _ = get_notification_settings()

        if work_hours_start <= now.time() < work_hours_end:
            logging.info("📢 Проверка новых заказов для отправки уведомлений...")
            await process_new_orders()
        else:
            logging.info("⏳ Вне рабочего времени. Новые уведомления не отправляются.")

        await asyncio.sleep(repeat_interval * 60)  # Ожидание перед проверкой новых заказов


async def send_repeat_notifications():
    """🔄 Запускает процесс проверки и отправки повторных уведомлений."""
    while True:
        now = datetime.now(MOSCOW_TZ)
        work_hours_start, work_hours_end, _, repeat_notified_interval = get_notification_settings()

        if work_hours_start <= now.time() < work_hours_end:
            logging.info("🔄 Проверка заказов для повторных уведомлений...")
            await process_notified_orders()
        else:
            logging.info("⏳ Вне рабочего времени. Повторные уведомления не отправляются.")

        await asyncio.sleep(repeat_notified_interval * 60)  # Ожидание перед повторными уведомлениями


def get_notification_settings():
    """🔍 Получает настройки уведомлений из БД и конвертирует `timedelta` в `time`."""
    with db_connect() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT work_hours_start, work_hours_end, repeat_interval, repeat_notified_interval 
            FROM notification_settings WHERE id = 1
        """)
        settings = cursor.fetchone()

        work_hours_start = (datetime.min + settings["work_hours_start"]).time()
        work_hours_end = (datetime.min + settings["work_hours_end"]).time()
        repeat_interval = settings["repeat_interval"]
        repeat_notified_interval = settings["repeat_notified_interval"]

    logging.debug(f"🛠 После конвертации: start={work_hours_start}, end={work_hours_end}")
    return work_hours_start, work_hours_end, repeat_interval, repeat_notified_interval


async def process_new_orders():
    """📩 Обрабатывает новые заказы `new` и отправляет первичные уведомления."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM pending_orders WHERE status = 'new'")
            new_orders = cursor.fetchall()

            logging.info(f"📌 Найдено {len(new_orders)} новых заказов для обработки.")

            if not new_orders:
                return

            for order in new_orders:
                logging.info(f"🔄 Обрабатываем заказ ID: {order['id']}")
                success = await notify_users(order, conn, cursor)

                if success:
                    cursor.execute(
                        "UPDATE pending_orders SET status = 'notified', last_notified_at = NOW() WHERE id = %s",
                        (order["id"],),
                    )
                    conn.commit()
                    logging.info(f"✅ Заказ {order['id']} обновлен до статуса 'notified'.")

    except Exception as e:
        logging.error(f"❌ Ошибка обработки новых заказов: {e}")


async def process_notified_orders():
    """🔄 Обрабатывает заказы `notified` и отправляет повторные уведомления."""
    try:
        now = datetime.now(MOSCOW_TZ)
        _, _, _, repeat_notified_interval = get_notification_settings()  # ✅ Получаем интервал

        check_time = now - timedelta(minutes=repeat_notified_interval)

        logging.info(f"🔍 Ищем заказы для повторного уведомления с временем <= {check_time}")

        with db_connect() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute(
                "SELECT * FROM pending_orders WHERE status = 'notified' AND last_notified_at <= %s",
                (check_time,),
            )
            notified_orders = cursor.fetchall()

            logging.info(f"🔁 Найдено {len(notified_orders)} заказов для повторного напоминания.")

            if not notified_orders:
                return

            for order in notified_orders:
                logging.info(f"🔄 Повторное уведомление для заказа ID: {order['id']}")
                success = await notify_users(order, conn, cursor, is_repeat=True)

                if success:
                    cursor.execute(
                        "UPDATE pending_orders SET last_notified_at = NOW() WHERE id = %s",
                        (order["id"],),
                    )
                    conn.commit()
                    logging.info(f"✅ Заказ {order['id']} обновлен (повторное напоминание).")

    except Exception as e:
        logging.error(f"❌ Ошибка обработки повторных уведомлений: {e}")


async def notify_users(order, conn, cursor, is_repeat=False):
    """📩 Отправляет уведомления пользователям."""
    message = format_order_message(order, is_repeat)
    success = False

    if order["send_to_executor"]:
        success = await send_to_role("4", message, cursor)

    if order["send_to_specialist"]:
        success = await send_to_role("3", message, cursor)

    return success


async def send_to_role(role, message, cursor):
    """🎯 Отправляет уведомления пользователям с указанной ролью."""
    try:
        cursor.execute("""
            SELECT telegram_id FROM users 
            WHERE role = %s AND telegram_id IS NOT NULL
            ORDER BY rating DESC
        """, (role,))
        users = cursor.fetchall()

        if not users:
            logging.warning(f"⚠️ Нет пользователей с ролью {role}")
            return False

        for user in users:
            try:
                await bot.send_message(chat_id=user["telegram_id"], text=message)
                await asyncio.sleep(1)
            except Exception as e:
                logging.error(f"❌ Ошибка отправки сообщения пользователю {user['telegram_id']}: {e}")

        logging.info(f"📩 Уведомления отправлены пользователям с ролью {role}")
        return True
    except Exception as e:
        logging.error(f"❌ Ошибка при обработке пользователей {role}: {e}")
        return False


def format_order_message(order, is_repeat=False):
    """📄 Формирует текст сообщения о заказе."""
    if is_repeat:
        return f"""
🔔 *Напоминание о заказе #{order['order_id']}*
📌 *Описание:* {order['short_description']}
💰 *Цена:* {order['price']} ₽
📅 *Выполнить до:* {order['deadline_at']}
⏳ *Заказ до сих пор свободен!*
"""
    else:
        return f"""
🚀 *Новый заказ #{order['order_id']}*
📌 *Описание:* {order['short_description']}
💰 *Цена:* {order['price']} ₽
📅 *Выполнить до:* {order['deadline_at']}
👀 *Кто первый возьмет заказ?*
"""


# 🚀 Запуск уведомлений
if __name__ == "__main__":
    logging.info("📢 Уведомления о заказах запущены в фоновом режиме!")

    loop = asyncio.get_event_loop()
    loop.create_task(send_notifications())  # ✅ Запускаем как фоновые задачи
    loop.create_task(send_repeat_notifications())
    loop.run_forever()  # ✅ Бесконечный цикл выполнения

