import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot_utils.bot_db_utils import db_connect


async def set_new_date(order_id, date):
    """
    Устанавливает новую дату выполнения/монтажа для заказа.
    """
    logging.info(f"Установка новой даты {date} для заказа {order_id}")
    with db_connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT montage_date FROM orders WHERE id = %s", (order_id,))
        current_date = cursor.fetchone()
        if current_date and current_date["montage_date"] is not None:
            raise ValueError(f"Дата уже установлена для заказа {order_id}: {current_date['montage_date']}")

        cursor.execute("UPDATE orders SET montage_date = %s WHERE id = %s", (date, order_id))
        conn.commit()
    logging.info(f"✅ Новая дата {date} успешно установлена для заказа {order_id}")


async def update_existing_date(order_id, date):
    """
    Обновляет существующую дату выполнения/монтажа для заказа.
    """
    logging.info(f"Обновление даты {date} для заказа {order_id}")
    with db_connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT montage_date FROM orders WHERE id = %s", (order_id,))
        current_date = cursor.fetchone()
        if not current_date or current_date["montage_date"] is None:
            raise ValueError(f"Дата не установлена для заказа {order_id}, используйте set_new_date")

        cursor.execute("UPDATE orders SET montage_date = %s WHERE id = %s", (date, order_id))
        conn.commit()
    logging.info(f"✅ Дата {date} успешно обновлена для заказа {order_id}")


async def handle_set_new_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для установки новой даты через Telegram.
    """
    order_id = context.user_data.get("current_order_id")
    date = update.message.text  # Получаем дату от пользователя
    try:
        await set_new_date(order_id, date)
        await update.message.reply_text(f"✅ Новая дата {date} успешно установлена для заказа {order_id}")
    except ValueError as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def handle_update_existing_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для изменения существующей даты через Telegram.
    """
    order_id = context.user_data.get("current_order_id")
    date = update.message.text  # Получаем дату от пользователя
    try:
        await update_existing_date(order_id, date)
        await update.message.reply_text(f"✅ Дата {date} успешно обновлена для заказа {order_id}")
    except ValueError as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
