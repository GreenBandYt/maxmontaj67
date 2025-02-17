# src/backend/telegram_bot/handlers/specialist/specialist_menu.py

from telegram import Update
from telegram.ext import ContextTypes
from .specialist_keyboards import specialist_keyboard

import logging
import pymysql
from bot_utils.bot_db_utils import db_connect
from telegram import ReplyKeyboardMarkup

from datetime import datetime, timedelta
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram_bot.bot_utils.messages.notifications import format_order_message  # Переиспользуем функцию
from telegram_bot.bot_utils.access_control import check_access, check_state
from telegram_bot.bot_utils.db_utils import update_user_state, get_user_role

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
    Отображение списка новых заданий для специалиста (отдельными сообщениями).
    """
    telegram_id = update.message.from_user.id
    logging.info(f"[SPECIALIST] {telegram_id} запросил список новых заданий.")

    with db_connect() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Получаем новые задания для специалиста
        cursor.execute("""
            SELECT * FROM pending_orders
            WHERE (status = 'new' OR status = 'notified')
              AND send_to_specialist = 1
        """)
        new_orders = cursor.fetchall()

        if not new_orders:
            await update.message.reply_text("🔔 На данный момент новых заданий нет.",
                                            reply_markup=specialist_keyboard())  # Обновляем клавиатуру
            return

        for order in new_orders:
            # Формируем сообщение и инлайн-кнопки
            message_text, reply_markup = format_order_message(order, is_repeat=False, role="3")
            if reply_markup:
                await update.message.reply_text(message_text, parse_mode="Markdown", reply_markup=reply_markup)
            else:
                await update.message.reply_text(message_text, parse_mode="Markdown")

async def handle_specialist_current_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает запрос на отображение текущих заданий для специалиста.
    """
    # Учитываем, что update может прийти из сообщения или из callback_query
    if update.message:
        telegram_id = update.message.from_user.id
    elif update.callback_query:
        telegram_id = update.callback_query.from_user.id
    else:
        logging.error("⚠ Неподдерживаемый тип update для handle_specialist_current_tasks.")
        return

    logging.info(f"[SPECIALIST] {telegram_id} запросил список текущих заданий.")

    with db_connect() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Запрос текущих заданий
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
            # Если вызов из сообщения или callback_query, отправляем сообщение корректно
            if update.message:
                await update.message.reply_text("🛠️ У вас нет текущих заданий.")
            elif update.callback_query:
                await update.callback_query.message.reply_text("🛠️ У вас нет текущих заданий.")
            return

        # Отправляем сообщение для каждого заказа
        for order in current_orders:
            message = f"""
📋 *Текущий заказ №{order['order_id']}*
🏠 *Адрес клиента:* {order['customer_address']}
📞 *Телефон клиента:* {order['customer_phone']}
📝 *Описание:* {order['description']}
📅 *Дата монтажа:* {order['montage_date'] or 'Не назначена'}
⏰ *Дедлайн:* {order['deadline_at']}
"""
            reply_markup = create_specialist_buttons(order["order_id"])

            # Если вызов из сообщения или callback_query, отправляем корректно
            if update.message:
                await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)
            elif update.callback_query:
                await update.callback_query.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)

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
    await query.edit_message_text(f"✅ Заказ #{order_id} принят в работу.")

async def handle_specialist_decline_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для кнопки "❌ Не принимаю" (специалист).
    """
    query = update.callback_query
    order_id = query.data.split("_")[-1]  # Получаем ID заказа

    logging.info(f"[SPECIALIST] {query.from_user.id} отказался от заказа {order_id}")

    await query.answer("❌ Вы отказались от заказа.", show_alert=True)
    await query.edit_message_reply_markup(None)  # Убираем кнопки

def create_specialist_buttons(order_id):
    """
    Создаёт кнопки для текущего задания специалиста.
    """
    buttons = [
        [
            InlineKeyboardButton("📅 Дата монтажа", callback_data=f"specialist_set_montage_date_{order_id}"),
            InlineKeyboardButton("✅ Завершение заказа", callback_data=f"specialist_complete_order_{order_id}")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

@check_state(required_state="specialist_idle")
async def handle_specialist_set_montage_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик кнопки "📅 Дата монтажа" для специалиста.
    Переход в режим "ввода даты монтажа".
    """
    query = update.callback_query
    callback_data = query.data
    order_id = int(callback_data.split("_")[-1])
    user_id = update.effective_user.id
    logging.info(f"[SPECIALIST] {user_id} выбрал настройку даты монтажа для заказа {order_id}")

    # Сохраняем order_id в user_data
    context.user_data["order_id"] = order_id

    # Получаем данные о заказе из базы данных
    with db_connect() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT 
                o.customer_address, 
                c.phone AS customer_phone, 
                o.montage_date, 
                o.description
            FROM 
                orders o
            JOIN 
                customers c ON o.customer_id = c.id
            WHERE 
                o.id = %s AND o.installer_id = (SELECT id FROM users WHERE telegram_id = %s)
        """, (order_id, user_id))
        order = cursor.fetchone()

    if not order:
        logging.error(f"[SPECIALIST] Заказ {order_id} не найден или не принадлежит пользователю {user_id}")
        await query.answer("❌ Ошибка: заказ не найден.", show_alert=True)
        return

    # Смена состояния
    await update_user_state(user_id, "specialist_date_input")
    logging.info(f"[SPECIALIST] Состояние пользователя {user_id} изменено на 'specialist_date_input'")

    # Отправляем сообщение с текущими данными о заказе
    await query.answer("Переключаемся в режим ввода даты монтажа.", show_alert=False)
    montage_date = order["montage_date"] or "Не назначена"
    await query.message.reply_text(
        f"📋 *Текущий заказ №{order_id}*\n"
        f"🏠 *Адрес клиента:* {order['customer_address']}\n"
        f"📞 *Телефон клиента:* {order['customer_phone']}\n"
        f"📅 *Дата монтажа:* {montage_date}\n"
        "\nВведите новую дату монтажа в формате: *YYYY-MM-DD*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["⬅️ Возврат в меню"]], resize_keyboard=True)
    )

@check_state("specialist_date_input")
async def handle_specialist_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает ввод даты монтажа от специалиста.
    """
    user_id = update.effective_user.id
    order_id = context.user_data.get("order_id")  # ID заказа сохраняется в user_data при выборе "Дата монтажа"
    input_text = update.message.text.strip()

    logging.info(f"[SPECIALIST] Пользователь {user_id} вводит дату монтажа для заказа {order_id}: '{input_text}'")

    # Проверяем формат даты
    try:
        montage_date = datetime.strptime(input_text, "%Y-%m-%d").date()
        context.user_data["montage_date"] = montage_date  # Сохраняем дату в user_data
    except ValueError:
        logging.warning(f"❌ Неверный формат даты от пользователя {user_id}: '{input_text}'")
        await update.message.reply_text(
            "❌ Неверный формат даты. Введите дату в формате YYYY-MM-DD, например: 2025-02-20."
        )
        return

    # Отправляем подтверждение с кнопками "Да" и "Нет"
    confirm_message = (
        f"Вы уверены, что хотите сохранить дату монтажа: *{montage_date.strftime('%Y-%m-%d')}*?"
    )
    confirm_buttons = [
        [
            InlineKeyboardButton("✅ Да", callback_data=f"specialist_confirm_date_input_{order_id}"),
            InlineKeyboardButton("❌ Нет", callback_data=f"specialist_cancel_date_input_{order_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(confirm_buttons)

    await update.message.reply_text(
        confirm_message,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    logging.info(f"✅ Введена дата {montage_date} для заказа {order_id}, ожидается подтверждение.")

@check_state(required_state="specialist_date_input")
async def handle_specialist_date_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает подтверждение сохранения даты монтажа от специалиста.
    """
    query = update.callback_query
    callback_data = query.data
    user_id = update.effective_user.id
    order_id = context.user_data.get("order_id")
    montage_date = context.user_data.get("montage_date")

    logging.info(f"[SPECIALIST] Пользователь {user_id} нажал подтверждение: {callback_data}.")

    # Проверяем наличие необходимых данных
    if not order_id or not montage_date:
        logging.error(f"[SPECIALIST] order_id или montage_date отсутствуют для пользователя {user_id}.")
        await query.answer("❌ Ошибка: данные заказа или дата отсутствуют. Попробуйте заново.", show_alert=True)
        return

    # Обрабатываем подтверждение
    if callback_data == f"specialist_confirm_date_input_{order_id}":
        # Сохраняем дату монтажа в БД
        try:
            with db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE orders SET montage_date = %s WHERE id = %s",
                    (montage_date, order_id)
                )
                conn.commit()

            logging.info(f"✅ Дата монтажа {montage_date} сохранена в БД для заказа {order_id}.")
            await query.answer("✅ Дата монтажа успешно сохранена.", show_alert=False)

            # Отправляем сообщение пользователю
            await query.edit_message_text(
                f"✅ Дата монтажа *{montage_date}* успешно сохранена для заказа №{order_id}.",
                parse_mode="Markdown"
            )

            # Возвращаем пользователя к списку задач
            await update_user_state(user_id, "specialist_idle")
            await handle_specialist_current_tasks(update, context)

        except Exception as e:
            logging.error(f"❌ Ошибка сохранения даты монтажа для заказа {order_id}: {e}")
            await query.answer("❌ Ошибка сохранения даты. Попробуйте снова.", show_alert=True)

    elif callback_data == f"specialist_cancel_date_input_{order_id}":
        # Пользователь отменил сохранение
        logging.info(f"[SPECIALIST] Пользователь {user_id} отменил сохранение даты для заказа {order_id}.")
        await query.answer("❌ Изменение даты отменено.", show_alert=False)

        # Возвращаем пользователя в режим ввода даты
        await update_user_state(user_id, "specialist_date_input")
        await query.message.reply_text(
            "Введите новую дату монтажа в формате YYYY-MM-DD или нажмите 'Назад в заказы'.",
            reply_markup=ReplyKeyboardMarkup([["⬅️ Возврат в меню"]], resize_keyboard=True)
        )

    else:
        logging.warning(f"[SPECIALIST] Неизвестное действие: {callback_data} для пользователя {user_id}.")
        await query.answer("❌ Неизвестное действие. Попробуйте снова.", show_alert=True)

@check_state(required_state="specialist_date_input")
async def handle_specialist_cancel_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает нажатие кнопки "Назад в заказы".
    Возвращает пользователя к списку текущих задач.
    """
    query = update.callback_query
    user_id = update.effective_user.id

    logging.info(f"[SPECIALIST] Пользователь {user_id} нажал кнопку 'Назад в заказы'.")

    # Меняем состояние пользователя на просмотр задач
    await update_user_state(user_id, "specialist_idle")
    logging.info(f"[SPECIALIST] Состояние пользователя {user_id} изменено на 'specialist_idle'.")

    # Уведомляем пользователя, что он возвращен к задачам
    await query.answer("Возвращаемся к списку заданий.", show_alert=False)

    # Вызываем функцию отображения списка текущих задач
    await handle_specialist_current_tasks(update, context)

async def handle_specialist_return_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает нажатие кнопки "⬅️ Возврат в меню".
    Перенаправляет пользователя в список новых заданий.
    """
    user_id = update.effective_user.id
    logging.info(f"[SPECIALIST] Пользователь {user_id} вернулся в меню.")

    # Обновляем состояние пользователя на стандартное
    await update_user_state(user_id, "specialist_idle")

    # Отправляем список новых заданий
    await handle_specialist_new_tasks(update, context)

