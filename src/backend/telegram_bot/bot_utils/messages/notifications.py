import os
import sys
import logging
import asyncio
import pymysql
import pytz

from datetime import datetime, timedelta
from telegram import Bot
from telegram_bot.bot_token import TELEGRAM_BOT_TOKEN

# Добавляем корневую папку "src" в sys.path, если нужно
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Импорт db_connect
from telegram_bot.bot_utils.bot_db_utils import db_connect

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# Инициализация бота
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Устанавливаем московский часовой пояс в Python
MOSCOW_TZ = pytz.timezone("Europe/Moscow")


async def notification_worker():
    """Фоновая задача по отправке уведомлений."""
    while True:
        now = datetime.now(MOSCOW_TZ)

        # Получаем настройки уведомлений из БД
        work_hours_start, work_hours_end, repeat_interval, repeat_notified_interval = get_notification_settings()

        # Определяем адаптивный интервал отправки
        adaptive_interval = repeat_interval

        # Если сегодня выходной (суббота или воскресенье)
        if now.weekday() in [5, 6]:
            logging.info("🚫 Выходной день! Интервал увеличен до 8 часов.")
            adaptive_interval = 8 * 60  # 8 часов в минутах

        # Если не в рабочее время
        if not (work_hours_start <= now.time() < work_hours_end):
            logging.info("⏳ Вне рабочего времени. Интервал увеличен до 30 минут.")
            adaptive_interval = 30  # 30 минут

        # Обработка новых и повторных уведомлений
        await process_new_orders()
        await process_notified_orders()

        logging.info(f"⏱ Текущий интервал отправки: {adaptive_interval} минут")
        await asyncio.sleep(adaptive_interval * 60)


def get_notification_settings():
    """Получает настройки уведомлений из БД и приводит рабочее время к типу time."""
    with db_connect() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT work_hours_start, work_hours_end, repeat_interval, repeat_notified_interval 
            FROM notification_settings WHERE id = 1
        """)
        settings = cursor.fetchone()

        # Если поля приходят как timedelta, то приводим их к типу time:
        if isinstance(settings["work_hours_start"], timedelta):
            work_hours_start = (datetime.min + settings["work_hours_start"]).time()
        else:
            work_hours_start = settings["work_hours_start"]

        if isinstance(settings["work_hours_end"], timedelta):
            work_hours_end = (datetime.min + settings["work_hours_end"]).time()
        else:
            work_hours_end = settings["work_hours_end"]

        repeat_interval = settings["repeat_interval"]
        repeat_notified_interval = settings["repeat_notified_interval"]

    logging.debug(f"Настройки: start={work_hours_start}, end={work_hours_end}, repeat={repeat_interval} мин.")
    return work_hours_start, work_hours_end, repeat_interval, repeat_notified_interval



async def process_new_orders():
    """Обрабатывает новые заказы и отправляет первичные уведомления."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            logging.info("Подключение к БД установлено. Запрос новых заказов...")
            cursor.execute("SELECT * FROM pending_orders WHERE status = 'new'")
            new_orders = cursor.fetchall()

            if not new_orders:
                logging.info("Нових заказов нет.")
                return

            for order in new_orders:
                logging.info(f"Новый заказ ID: {order['id']} -> Отправка уведомлений")
                success = await notify_users(order, cursor)

                logging.info(f"Статус отправки заказа ID {order['id']}: {success}")

                if success:
                    try:
                        logging.info(f"Обновление статуса заказа ID {order['id']}")
                        cursor.execute("""
                            UPDATE pending_orders 
                            SET last_notified_at = NOW()
                            WHERE id = %s
                        """, (order["id"],))
                        conn.commit()
                        logging.info(f"Заказ ID {order['id']} обновлён до 'notified'")
                    except Exception as e:
                        logging.error(f"Ошибка обновления заказа ID {order['id']}: {e}")

    except Exception as e:
        logging.error(f"Ошибка обработки новых заказов: {e}")


async def process_notified_orders():
    """Обрабатывает заказы с статусом 'notified' для повторных уведомлений."""
    try:
        now = datetime.now(MOSCOW_TZ)
        _, _, _, repeat_notified_interval = get_notification_settings()
        check_time = now - timedelta(minutes=repeat_notified_interval, seconds=5)

        with db_connect() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT * FROM pending_orders 
                WHERE status = 'notified' AND last_notified_at <= %s
            """, (check_time,))
            notified_orders = cursor.fetchall()

            if not notified_orders:
                return

            for order in notified_orders:
                logging.info(f"Повторное уведомление для заказа ID: {order['id']}")
                success = await notify_users(order, cursor, is_repeat=True)

                if success:
                    cursor.execute("""
                        UPDATE pending_orders 
                        SET last_notified_at = NOW()
                        WHERE id = %s
                    """, (order["id"],))
                    conn.commit()

    except Exception as e:
        logging.error(f"Ошибка обработки повторных уведомлений: {e}")


async def notify_users(order, cursor, is_repeat=False):
    """Отправляет уведомления пользователям."""
    message = format_order_message(order, is_repeat)
    success = False

    if order["send_to_executor"]:
        result = await send_to_role("4", message, cursor)
        if result:
            success = True

    if order["send_to_specialist"]:
        result = await send_to_role("3", message, cursor)
        if result:
            success = True

    logging.info(f"notify_users для ID {order['id']} завершён с результатом {success}")
    return success


async def send_to_role(role, message, cursor):
    """Отправляет уведомления пользователям с указанной ролью."""
    try:
        cursor.execute("""
            SELECT telegram_id FROM users 
            WHERE role = %s AND telegram_id IS NOT NULL
            ORDER BY rating DESC
        """, (role,))
        users = cursor.fetchall()

        if not users:
            logging.warning(f"Нет пользователей с ролью {role}")
            return False

        for user in users:
            try:
                await bot.send_message(chat_id=user["telegram_id"], text=message)
                await asyncio.sleep(1)
                return True
            except Exception as e:
                logging.error(f"Ошибка отправки пользователю {user['telegram_id']}: {e}")

        return False

    except Exception as e:
        logging.error(f"Ошибка отправки уведомлений пользователям с ролью {role}: {e}")
        return False


def format_order_message(order, is_repeat=False):
    """Формирует текст сообщения о заказе."""
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


# Запуск уведомлений в фоне
if __name__ == "__main__":
    logging.info("Уведомления запущены!")
    loop = asyncio.get_event_loop()
    loop.create_task(notification_worker())
    loop.run_forever()
