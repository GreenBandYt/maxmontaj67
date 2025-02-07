from telegram import Update
from telegram.ext import ContextTypes
from .specialist_keyboards import specialist_keyboard

import logging
import pymysql
from bot_utils.bot_db_utils import db_connect


async def specialist_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Стартовая страница для специалиста.
    """
    await update.message.reply_text(
        f"Добро пожаловать, {update.effective_user.first_name}!\n"
        "Вы вошли как Специалист.\n"
        "Что вы хотите сделать?",
        reply_markup=specialist_keyboard()  # Клавиатура для специалиста
    )

async def handle_specialist_new_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка кнопки "📋 Новые задания".
    """
    await update.message.reply_text("Показать новые задания для специалиста.")

async def handle_specialist_current_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка кнопки "🗂️ Текущие задания".
    """
    await update.message.reply_text("Показать текущие задания для специалиста.")

async def handle_specialist_contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка кнопки "✉️ Связаться".
    """
    await update.message.reply_text("Свяжитесь с администратором, чтобы решить вашу проблему.")


async def handle_specialist_accept_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    order_id = int(query.data.split("_")[-1])
    telegram_id = query.from_user.id

    logging.info(f"[SPECIALIST] {telegram_id} пытается принять заказ {order_id}")

    with db_connect() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Проверяем статус заказа
        cursor.execute("SELECT status FROM orders WHERE id = %s", (order_id,))
        order = cursor.fetchone()

        if not order:
            logging.error(f"[SPECIALIST] Заказ {order_id} не найден в БД!")
            await query.answer("❌ Ошибка: заказ не найден.", show_alert=True)
            await query.edit_message_text("❌ Ошибка: заказ не найден. Возможно, он уже удалён.")
            return

        if order["status"] == "Выполняется":
            logging.warning(f"[SPECIALIST] Заказ {order_id} уже выполняется!")
            await query.answer("⚠️ Этот заказ уже выполняется!", show_alert=True)
            await query.edit_message_text("⚠️ Этот заказ уже выполняется! Обновите список доступных заказов.")
            return

        # Находим user_id по telegram_id
        cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
        user = cursor.fetchone()

        if not user:
            logging.error(f"[SPECIALIST] Пользователь с telegram_id {telegram_id} не найден в БД!")
            await query.answer("❌ Ошибка: ваш аккаунт не зарегистрирован.", show_alert=True)
            return

        user_id = user["id"]
        logging.info(f"[SPECIALIST] Найден user_id {user_id} для telegram_id {telegram_id}")

        # Обновляем заказ
        sql = "UPDATE orders SET installer_id = %s, status = 'Выполняется' WHERE id = %s"
        logging.info(f"SQL QUERY: {sql} | DATA: ({user_id}, {order_id})")
        cursor.execute(sql, (user_id, order_id))
        conn.commit()
        logging.info("✅ Данные успешно записаны в БД")

        # Удаляем заказ из pending_orders
        cursor.execute("DELETE FROM pending_orders WHERE order_id = %s", (order_id,))
        conn.commit()
        logging.info(f"🗑️ Заказ {order_id} удалён из pending_orders")

    await query.answer("✅ Вы приняли заказ в работу!", show_alert=True)
    await query.edit_message_reply_markup(None)





async def handle_specialist_decline_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для кнопки "❌ Не принимаю" (специалист).
    """
    query = update.callback_query
    order_id = query.data.split("_")[-1]  # Получаем ID заказа

    logging.info(f"[SPECIALIST] {query.from_user.id} отказался от заказа {order_id}")

    await query.answer("❌ Вы отказались от заказа.", show_alert=True)
    await query.edit_message_reply_markup(None)  # Убираем кнопки
