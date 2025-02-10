# src/backend/telegram_bot/handlers/executor/executor_menu.py

from telegram import Update
from telegram.ext import ContextTypes
from .executor_keyboards import executor_keyboard
import logging
import pymysql
from datetime import datetime, timedelta
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from telegram_bot.bot_utils.bot_db_utils import db_connect
from telegram_bot.bot_utils.messages.notifications import format_order_message  # Переиспользуем функцию

async def executor_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Стартовая страница для исполнителя.
    """
    await update.message.reply_text(
        f"Добро пожаловать, {update.effective_user.first_name}!\n"
        "Вы вошли как Исполнитель.\n"
        "Выберите действие из меню ниже:",
        reply_markup=executor_keyboard()  # Клавиатура для исполнителя
    )




async def handle_executor_accept_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    order_id = int(query.data.split("_")[-1])
    telegram_id = query.from_user.id

    logging.info(f"[EXECUTOR] {telegram_id} пытается взять заказ {order_id}")

    with db_connect() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Проверяем статус заказа
        cursor.execute("SELECT status FROM orders WHERE id = %s", (order_id,))
        order = cursor.fetchone()

        if not order:
            logging.error(f"[EXECUTOR] Заказ {order_id} не найден в БД!")
            await query.answer("❌ Ошибка: заказ не найден.", show_alert=True)
            await query.edit_message_text("❌ Ошибка: заказ не найден. Возможно, он уже удалён.")
            return

        if order["status"] == "Выполняется":
            logging.warning(f"[EXECUTOR] Заказ {order_id} уже выполняется!")
            await query.answer("⚠️ Этот заказ уже выполняется!", show_alert=True)
            await query.edit_message_text("⚠️ Этот заказ уже выполняется! Обновите список доступных заказов.")
            return

        # Находим user_id по telegram_id
        cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
        user = cursor.fetchone()

        if not user:
            logging.error(f"[EXECUTOR] Пользователь с telegram_id {telegram_id} не найден в БД!")
            await query.answer("❌ Ошибка: ваш аккаунт не зарегистрирован.", show_alert=True)
            return

        user_id = user["id"]
        logging.info(f"[EXECUTOR] Найден user_id {user_id} для telegram_id {telegram_id}")

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

    await query.edit_message_text("✅ Заказ успешно взят в работу!")  # Изменение текста исходного сообщения
    await query.edit_message_reply_markup(None)


async def handle_executor_decline_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для кнопки "🔙 Не беру" (исполнитель).
    """
    query = update.callback_query
    order_id = query.data.split("_")[-1]  # Получаем ID заказа

    logging.info(f"[EXECUTOR] {query.from_user.id} отказался от заказа {order_id}")

    await query.answer("🚫 Вы отказались от заказа.", show_alert=True)
    await query.edit_message_reply_markup(None)  # Убираем кнопки


async def handle_executor_new_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение списка новых заданий для исполнителя (отдельными сообщениями).
    """
    telegram_id = update.message.from_user.id  # Получаем telegram_id пользователя
    logging.info(f"[EXECUTOR] {telegram_id} запросил список новых заданий.")

    with db_connect() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Получаем список новых заданий из pending_orders
        cursor.execute("""
            SELECT * FROM pending_orders
            WHERE (status='new' OR status='notified')
        """)
        new_orders = cursor.fetchall()

        if not new_orders:
            await update.message.reply_text("🔔 На данный момент новых заданий нет.")
            return

        # Отправляем каждое задание отдельным сообщением
        for order in new_orders:
            # Форматируем сообщение и кнопки через уже существующую функцию
            message_text, reply_markup = format_order_message(order, is_repeat=False, role="4")

            # Отправляем сообщение с кнопками
            if reply_markup:
                await update.message.reply_text(message_text, parse_mode="Markdown", reply_markup=reply_markup)
            else:
                await update.message.reply_text(message_text, parse_mode="Markdown")

async def handle_executor_current_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение списка текущих заданий для исполнителя.
    """
    telegram_id = update.message.from_user.id  # Получаем telegram_id пользователя
    logging.info(f"[EXECUTOR] {telegram_id} запросил список текущих заданий.")

    with db_connect() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Исправленный запрос текущих заданий
        cursor.execute("""
            SELECT 
                o.id AS order_id, 
                o.customer_address, 
                c.phone AS customer_phone, 
                o.description, 
                o.montage_date, 
                o.deadline_at 
            FROM 
                orders o
            JOIN 
                customers c ON o.customer_id = c.id
            WHERE 
                o.installer_id = (SELECT id FROM users WHERE telegram_id = %s) AND 
                o.status = 'Выполняется'
        """, (telegram_id,))
        current_orders = cursor.fetchall()

        if not current_orders:
            await update.message.reply_text("🛠️ У вас нет текущих заданий.")
            return

        # Отправляем сообщение для каждого заказа
        for order in current_orders:
            message = f"""
📋 *Текущее задание №{order['order_id']}*
🏠 *Адрес клиента:* {order['customer_address']}
📞 *Телефон клиента:* {order['customer_phone']}
📝 *Описание:* {order['description']}
📅 *Дата выполнения:* {order['montage_date'] or 'Не назначена'}
⏰ *Дедлайн:* {order['deadline_at']}
"""
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📅 Дата выполнения", callback_data=f"executor_set_montage_date_{order['order_id']}"),
                    InlineKeyboardButton("✅ Закрытие заказа", callback_data=f"executor_complete_order_{order['order_id']}")
                ]
            ])
            await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)







async def handle_executor_montage_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Заглушка для меню управления датой выполнения (executor).
    """
    await update.message.reply_text("📅 Меню управления датой выполнения пока в разработке.")

async def handle_executor_complete_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Заглушка для меню завершения заказа (executor).
    """
    await update.message.reply_text("✅ Меню завершения заказа пока в разработке.")



async def handle_executor_contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Вы можете написать администратору прямо здесь.")