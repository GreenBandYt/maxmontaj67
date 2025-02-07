from telegram import Update
from telegram.ext import ContextTypes
from .executor_keyboards import executor_keyboard
import logging
import pymysql
from bot_utils.bot_db_utils import db_connect

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

async def handle_executor_new_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Здесь отображаются новые задания.")

async def handle_executor_current_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Вот список ваших текущих заданий.")

async def handle_executor_contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Вы можете написать администратору прямо здесь.")


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

    await query.answer("✅ Вы взяли заказ в работу!", show_alert=True)
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
