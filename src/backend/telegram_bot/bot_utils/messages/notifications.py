import os
import sys
import logging
import asyncio
import pymysql
import pytz

from datetime import datetime, timedelta
from telegram import Bot
from telegram_bot.bot_token import TELEGRAM_BOT_TOKEN

# Добавляем корневую папку "src" в sys.path при необходимости
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Импорт db_connect
from telegram_bot.bot_utils.bot_db_utils import db_connect

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# Инициализация бота
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Устанавливаем московский часовой пояс
MOSCOW_TZ = pytz.timezone("Europe/Moscow")


async def notification_worker():
    """
    Фоновая задача по отправке уведомлений.
    Каждые repeat_interval (или адаптивный) минут:
      1) process_new_orders()      - новые заказы
      2) process_notified_orders() - повторные уведомления
      3) process_deadline_orders() - предупреждение о дедлайне
    """
    while True:
        now = datetime.now(MOSCOW_TZ)

        # Получаем все настройки
        work_hours_start, work_hours_end, repeat_interval, repeat_notified_interval, deadline_warning_days = get_notification_settings()

        # По умолчанию берём repeat_interval
        adaptive_interval = repeat_interval

        # Если выходной (сб, вс)
        if now.weekday() in [5, 6]:
            logging.info("🚫 Выходной день! Интервал увеличен до 8 часов.")
            adaptive_interval = 8 * 60

        # Вне рабочего времени
        if not (work_hours_start <= now.time() < work_hours_end):
            logging.info("⏳ Вне рабочего времени. Интервал увеличен до 30 минут.")
            adaptive_interval = 30

        # 1) Новые заказы
        await process_new_orders()
        # 2) Повторные уведомления
        await process_notified_orders()
        # 3) Проверка дедлайна
        await process_deadline_orders(deadline_warning_days)

        logging.info(f"⏱ Текущий интервал отправки: {adaptive_interval} минут")
        await asyncio.sleep(adaptive_interval * 60)


def get_notification_settings():
    """
    Получает настройки уведомлений из БД: work_hours_start/end, repeat_interval,
    repeat_notified_interval, deadline_warning_days.
    Приводит work_hours_... к time, если это timedelta.
    Возвращает (work_hours_start, work_hours_end, repeat_interval,
                repeat_notified_interval, deadline_warning_days).
    """
    with db_connect() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT work_hours_start, work_hours_end,
                   repeat_interval, repeat_notified_interval,
                   deadline_warning_days
            FROM notification_settings
            WHERE id = 1
        """)
        settings = cursor.fetchone()

        # Преобразуем в time, если пришло как timedelta
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
        deadline_warning_days = settings["deadline_warning_days"]

    logging.debug(
        f"Настройки: start={work_hours_start}, end={work_hours_end}, "
        f"repeat={repeat_interval} мин, repeat_notified={repeat_notified_interval}, "
        f"deadline_warning={deadline_warning_days} дн."
    )
    return work_hours_start, work_hours_end, repeat_interval, repeat_notified_interval, deadline_warning_days


async def process_new_orders():
    """
    Обрабатывает заказы (status='new') и отправляет первичные уведомления.
    После успешной отправки => ставим last_notified_at=NOW(), status='notified'.
    Если нет пользователей или не получилось никому отправить,
    всё равно переводим заказ в 'notified', чтобы не застревал в 'new'.
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            logging.info("Подключение к БД установлено. Запрос новых заказов...")
            cursor.execute("SELECT * FROM pending_orders WHERE status='new'")
            new_orders = cursor.fetchall()

            if not new_orders:
                logging.info("Новых заказов нет.")
                return

            for order in new_orders:
                logging.info(f"Новый заказ ID: {order['id']} -> отправляем первичное уведомление")
                success = await notify_users(order, cursor)

                logging.info(f"Статус отправки заказа ID {order['id']}: {success}")

                # Независимо от success, чтобы заказ не висел в new
                try:
                    logging.info(f"Обновляем last_notified_at и статус заказа ID {order['id']}")
                    cursor.execute("""
                        UPDATE pending_orders
                        SET last_notified_at = NOW(),
                            status='notified'
                        WHERE id = %s
                    """, (order["id"],))
                    conn.commit()
                    logging.info(f"Заказ ID {order['id']} теперь status='notified'")
                except Exception as e:
                    logging.error(f"Ошибка обновления заказа ID {order['id']}: {e}")

    except Exception as e:
        logging.error(f"Ошибка обработки новых заказов: {e}")


async def process_notified_orders():
    """
    Обрабатывает заказы со статусом 'notified', отправляет повторные уведомления
    если прошло repeat_notified_interval минут с момента last_notified_at.
    """
    try:
        now = datetime.now(MOSCOW_TZ)
        # Берём repeat_notified_interval
        _, _, _, repeat_notified_interval, _ = get_notification_settings()

        check_time = now - timedelta(minutes=repeat_notified_interval, seconds=5)

        with db_connect() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT * FROM pending_orders
                WHERE status='notified'
                  AND last_notified_at <= %s
            """, (check_time,))
            notified_orders = cursor.fetchall()

            if not notified_orders:
                return

            for order in notified_orders:
                logging.info(f"Повторное уведомление для заказа ID: {order['id']}")
                success = await notify_users(order, cursor, is_repeat=True)
                # Если success — обновляем last_notified_at
                # (Иначе не трогаем, чтобы при следующем цикле снова попытаться)
                if success:
                    cursor.execute("""
                        UPDATE pending_orders
                        SET last_notified_at = NOW()
                        WHERE id = %s
                    """, (order["id"],))
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
    """
    Отправляем уведомления пользователям (исполнителям/специалистам).
    Если нет никого (или рассылка не удалась), success=False.
    """
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

    logging.info(f"notify_users завершён для ID {order['id']} с результатом {success}")
    return success


async def send_to_role(role, message, cursor):
    """
    Рассылаем сообщение пользователям с заданной ролью.
    Возвращаем True, если удалось отправить хотя бы одному.
    """
    try:
        cursor.execute("""
            SELECT telegram_id
            FROM users
            WHERE role = %s
              AND telegram_id IS NOT NULL
            ORDER BY rating DESC
        """, (role,))
        users = cursor.fetchall()

        if not users:
            logging.warning(f"Нет пользователей с ролью {role}")
            return False

        # Логика: отправим первому успешному (остальным нет)
        for user in users:
            try:
                await bot.send_message(chat_id=user["telegram_id"], text=message, parse_mode="Markdown")
                await asyncio.sleep(1)
                return True
            except Exception as e:
                logging.error(f"Ошибка отправки пользователю {user['telegram_id']}: {e}")

        return False

    except Exception as e:
        logging.error(f"Ошибка при рассылке пользователям role={role}: {e}")
        return False


def format_order_message(order, is_repeat=False):
    """
    Формируем текст для исполнителей/специалистов о заказе. Markdown-формат.
    """
    if is_repeat:
        return f"""
🔔 *Напоминание о заказе #{order['order_id']}*
📌 *Описание:* {order['short_description']}
💰 *Цена:* {order['price']} ₽
📅 *Выполнить до:* {order['deadline_at']}
⏳ *Заказ до сих пор не взят никем в работу!*
"""
    else:
        return f"""
🚀 *Новый заказ #{order['order_id']}*
📌 *Описание:* {order['short_description']}
💰 *Цена:* {order['price']} ₽
📅 *Выполнить до:* {order['deadline_at']}
👀 *Кто первый возьмет заказ?*
"""


# Запуск уведомлений
if __name__ == "__main__":
    logging.info("Уведомления запущены!")
    loop = asyncio.get_event_loop()
    loop.create_task(notification_worker())
    loop.run_forever()
