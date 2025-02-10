import os
import sys
import logging
import asyncio
import pymysql
import pytz

from datetime import datetime, timedelta
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram_bot.bot_token import TELEGRAM_BOT_TOKEN

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from telegram_bot.bot_utils.bot_db_utils import db_connect


logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
bot = Bot(token=TELEGRAM_BOT_TOKEN)
MOSCOW_TZ = pytz.timezone("Europe/Moscow")


async def notification_worker():
    while True:
        now = datetime.now(MOSCOW_TZ)
        work_hours_start, work_hours_end, repeat_interval, repeat_notified_interval, deadline_warning_days = get_notification_settings()
        adaptive_interval = repeat_interval

        if now.weekday() in [5, 6]:
            adaptive_interval = 8 * 60
            logging.info("🚫 Выходной день! Интервал увеличен до 8 часов.")

        if not (work_hours_start <= now.time() < work_hours_end):
            adaptive_interval = 30
            logging.info("⏳ Вне рабочего времени. Интервал увеличен до 30 минут.")

        await process_new_orders()
        await process_notified_orders()
        await process_deadline_orders(deadline_warning_days)

        logging.info(f"⏱ Текущий интервал отправки: {adaptive_interval} минут")
        await asyncio.sleep(adaptive_interval * 60)


def get_notification_settings():
    with db_connect() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM notification_settings WHERE id = 1")
        settings = cursor.fetchone()

        # Преобразуем значения времени из timedelta в datetime.time
        work_hours_start = settings["work_hours_start"]
        if isinstance(work_hours_start, timedelta):
            work_hours_start = (datetime.min + work_hours_start).time()

        work_hours_end = settings["work_hours_end"]
        if isinstance(work_hours_end, timedelta):
            work_hours_end = (datetime.min + work_hours_end).time()

        return (
            work_hours_start,
            work_hours_end,
            settings["repeat_interval"],
            settings["repeat_notified_interval"],
            settings["deadline_warning_days"]
        )


async def process_new_orders():
    try:
        with db_connect() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM pending_orders WHERE status='new'")
            new_orders = cursor.fetchall()

            for order in new_orders:
                success = await notify_users(order, cursor)
                cursor.execute("UPDATE pending_orders SET last_notified_at=NOW(), status='notified' WHERE id=%s",
                               (order["id"],))
                conn.commit()
    except Exception as e:
        logging.error(f"Ошибка обработки новых заказов: {e}")


async def process_notified_orders():
    try:
        now = datetime.now(MOSCOW_TZ)
        _, _, _, repeat_notified_interval, _ = get_notification_settings()
        check_time = now - timedelta(minutes=repeat_notified_interval, seconds=5)

        with db_connect() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM pending_orders WHERE status='notified' AND last_notified_at <= %s",
                           (check_time,))
            notified_orders = cursor.fetchall()

            for order in notified_orders:
                success = await notify_users(order, cursor, is_repeat=True)
                if success:
                    cursor.execute("UPDATE pending_orders SET last_notified_at=NOW() WHERE id=%s", (order["id"],))
                    conn.commit()
    except Exception as e:
        logging.error(f"Ошибка обработки повторных уведомлений: {e}")


async def process_deadline_orders(deadline_warning_days):
    """
    Предупреждаем администраторов (role='admin') о заказах,
    у которых дедлайн <= (текущее время + deadline_warning_days).
    """

    try:
        now = datetime.now(MOSCOW_TZ)
        warning_threshold = now + timedelta(days=deadline_warning_days)

        logging.info(f"🔎 Проверяем заказы с дедлайном до {warning_threshold}")

        with db_connect() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # Логируем SQL-запрос
            cursor.execute("""
                SELECT * FROM pending_orders
                WHERE (status='new' OR status='notified')
                  AND deadline_at <= %s
            """, (warning_threshold,))
            deadline_orders = cursor.fetchall()

            logging.info(f"📊 Найдено заказов с дедлайном: {len(deadline_orders)}")
            if not deadline_orders:
                return

            # Получаем список админов
            cursor.execute("""
                SELECT telegram_id
                FROM users
                WHERE role= 1
                  AND telegram_id IS NOT NULL
            """)
            admins = cursor.fetchall()

            logging.info(f"👤 Найдено админов для уведомления: {len(admins)}")

            # Шлём каждому админу сообщение по каждому заказу
            for order in deadline_orders:
                message = format_deadline_warning_message(order, deadline_warning_days)
                for adm in admins:
                    if adm["telegram_id"]:
                        logging.info(f"📤 Отправляем уведомление админу {adm['telegram_id']} по заказу ID {order['id']}")
                        try:
                            await bot.send_message(
                                chat_id=adm["telegram_id"],
                                text=message,
                                parse_mode="Markdown"
                            )
                            await asyncio.sleep(1)
                        except Exception as e:
                            logging.error(f"❌ Ошибка отправки админу {adm['telegram_id']}: {e}")

    except Exception as e:
        logging.error(f"❌ Ошибка при отправке уведомлений о дедлайне: {e}")

def format_deadline_warning_message(order, deadline_warning_days):
    """
    Формируем сообщение для админа о приближающемся дедлайне.
    """
    return f"""
🔔 *Напоминание о заказе #{order['order_id']}*
📌 *Описание:* {order['short_description']}
💰 *Цена:* {order['price']} ₽
📅 *Выполнить до:* {order['deadline_at']}
⏳ *Дедлайн наступает в ближайшие {deadline_warning_days} дн! Заказ до сих пор не взят!*
"""

async def notify_users(order, cursor, is_repeat=False):
    success = False
    if order["send_to_executor"]:
        success |= await send_to_role("4", order, is_repeat, cursor)
    if order["send_to_specialist"]:
        success |= await send_to_role("3", order, is_repeat, cursor)
    return success


async def send_to_role(role, order, is_repeat, cursor):
    try:
        message_text, reply_markup = format_order_message(order, is_repeat, role)
        cursor.execute("SELECT telegram_id FROM users WHERE role=%s AND telegram_id IS NOT NULL ORDER BY rating DESC",
                       (role,))
        users = cursor.fetchall()

        for user in users:
            try:
                await bot.send_message(
                    chat_id=user["telegram_id"],
                    text=message_text,
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
                await asyncio.sleep(1)
                return True
            except Exception as e:
                logging.error(f"Ошибка отправки пользователю {user['telegram_id']}: {e}")
        return False
    except Exception as e:
        logging.error(f"Ошибка при рассылке role={role}: {e}")
        return False


def format_order_message(order, is_repeat, role):
    """
    Формирует текст уведомления о заказе и инлайн-кнопки.
    """
    if is_repeat:
        text = f"""🔔 *Напоминание о заказе #{order['order_id']}*
📌 *Описание:* {order['short_description']}
💰 *Цена:* {order['price']} ₽
📅 *Выполнить до:* {order['deadline_at']}"""
    else:
        text = f"""🚀 *Новый заказ #{order['order_id']}*
📌 *Описание:* {order['short_description']}
💰 *Цена:* {order['price']} ₽
📅 *Выполнить до:* {order['deadline_at']}"""

    keyboard = []

    if role == '4':  # Исполнитель (монтажник)
        keyboard.append([
            InlineKeyboardButton("🛠️ Взять в работу", callback_data=f"executor_accept_order_{order['order_id']}"),
            InlineKeyboardButton("🔙 Не беру", callback_data=f"executor_decline_order_{order['order_id']}")
        ])
    elif role == '3':  # Специалист
        keyboard.append([
            InlineKeyboardButton("📌 Принять в работу", callback_data=f"specialist_accept_order_{order['order_id']}"),
            InlineKeyboardButton("❌ Не принимаю", callback_data=f"specialist_decline_order_{order['order_id']}")
        ])

    return text, InlineKeyboardMarkup(keyboard) if keyboard else None



if __name__ == "__main__":
    logging.info("Уведомления запущены!")
    loop = asyncio.get_event_loop()
    loop.create_task(notification_worker())
    loop.run_forever()