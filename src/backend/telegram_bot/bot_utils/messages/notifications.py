import os
import sys
import logging
import asyncio
import pymysql  # ✅ Добавляем импорт

from datetime import datetime
from telegram import Bot
from telegram_bot.bot_token import TELEGRAM_BOT_TOKEN

# ✅ Добавляем корневую папку "src" в `sys.path`
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ✅ Теперь импорт `db_connect` должен работать
from telegram_bot.bot_utils.bot_db_utils import db_connect


# 🛠 Настройка логирования
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# 📢 Инициализация бота
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# ⏳ Рабочие часы отправки уведомлений
WORK_HOURS = (8, 20)  # Уведомления с 08:00 до 20:00

async def send_notifications():
    """
    🔄 Запускает процесс проверки и отправки уведомлений.
    Проверяет новые заказы и отправляет сообщения в рабочие часы.
    """
    while True:
        now = datetime.now()
        if WORK_HOURS[0] <= now.hour < WORK_HOURS[1]:  # Проверка рабочего времени
            logging.info("📢 Проверка новых заказов для отправки уведомлений...")
            await process_new_orders()
        else:
            logging.info("⏳ Вне рабочего времени. Уведомления не отправляются.")

        await asyncio.sleep(60)  # Проверка каждые 60 секунд

async def process_new_orders():
    """Обрабатывает новые заказы в `pending_orders` и отправляет уведомления."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)  # ✅ Оставляем DictCursor
            cursor.execute("SELECT * FROM pending_orders WHERE status = 'new'")
            new_orders = cursor.fetchall()

            logging.info(f"📌 Найдено {len(new_orders)} новых заказов для обработки.")

            if not new_orders:
                logging.info("✅ Нет новых заказов для отправки.")
                return

            for order in new_orders:
                logging.info(f"🔄 Обрабатываем заказ ID: {order['id']}")
                await notify_users(order, conn, cursor)

    except Exception as e:
        logging.error(f"❌ Ошибка обработки новых заказов: {e}")



async def notify_users(order, conn, cursor):
    """
    📩 Отправляет уведомления пользователям и обновляет статус заказа.
    """
    message = format_order_message(order)
    success = False

    # Отправляем исполнителям
    if order["send_to_executor"]:
        success = await send_to_role("4", message, cursor)

    # Отправляем специалистам
    if order["send_to_specialist"]:
        success = await send_to_role("3", message, cursor)

    # ✅ Если уведомление отправлено, обновляем статус заказа
    if success:
        cursor.execute(
            "UPDATE pending_orders SET status = 'notified' WHERE id = %s", (order["id"],)
        )
        conn.commit()
        logging.info(f"🔄 Заказ {order['id']} переведен в статус 'notified'")

async def send_to_role(role, message, cursor):
    """
    🎯 Отправляет уведомления пользователям с указанной ролью.
    """
    try:
        cursor.execute(
            """
            SELECT telegram_id FROM users 
            WHERE role = %s AND telegram_id IS NOT NULL
            ORDER BY rating DESC
            """,
            (role,),
        )
        users = cursor.fetchall()

        if not users:
            logging.warning(f"⚠️ Нет пользователей с ролью {role}")
            return False

        for user in users:
            try:
                await bot.send_message(chat_id=user["telegram_id"], text=message)
                await asyncio.sleep(1)  # ⏳ Задержка между отправками
            except Exception as e:
                logging.error(f"❌ Ошибка отправки сообщения пользователю {user['telegram_id']}: {e}")

        logging.info(f"📩 Уведомления отправлены пользователям с ролью {role}")
        return True
    except Exception as e:
        logging.error(f"❌ Ошибка при обработке пользователей {role}: {e}")
        return False

def format_order_message(order):
    """
    📄 Формирует текст сообщения о новом заказе.
    """
    return f"""
🚀 *Новый заказ #{order['order_id']}*
📌 *Описание:* {order['short_description']}
💰 *Цена:* {order['price']} ₽
📅 *Дедлайн:* {order['deadline_at']}
👀 *Кто первый возьмет заказ?*
"""

# 🚀 Запуск уведомлений
if __name__ == "__main__":
    logging.info("📢 Уведомления о заказах запущены в фоновом режиме!")
    asyncio.run(send_notifications())
