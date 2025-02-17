# src/backend/telegram_bot/handlers/executor/executor_menu.py

from telegram import Update
from telegram.ext import ContextTypes
from .executor_keyboards import executor_keyboard

import logging
import pymysql
from bot_utils.bot_db_utils import db_connect
from telegram import ReplyKeyboardMarkup

from datetime import datetime, timedelta
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram_bot.bot_utils.messages.notifications import format_order_message  # Переиспользуем функцию
from telegram_bot.bot_utils.access_control import check_access, check_state
from telegram_bot.bot_utils.db_utils import update_user_state, get_user_role

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
            await update.message.reply_text("🔔 На данный момент новых заданий нет.",
                                            reply_markup=executor_keyboard())
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
    Обрабатывает запрос на отображение текущих заданий для исполнителя.
    """
    # Учитываем, что update может прийти из сообщения или из callback_query
    if update.message:
        telegram_id = update.message.from_user.id
    elif update.callback_query:
        telegram_id = update.callback_query.from_user.id
    else:
        logging.error("⚠ Неподдерживаемый тип update для handle_executor_current_tasks.")
        return

    logging.info(f"[EXECUTOR] {telegram_id} запросил список текущих заданий.")

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
            reply_markup = create_executor_buttons(order["order_id"])

            # Если вызов из сообщения или callback_query, отправляем корректно
            if update.message:
                await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)
            elif update.callback_query:
                await update.callback_query.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)

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

def create_executor_buttons(order_id):
    """
    Создаёт кнопки для текущего задания исполнителя.
    """
    buttons = [
        [
            InlineKeyboardButton("📅 Дата выполнения", callback_data=f"executor_set_montage_date_{order_id}"),
            InlineKeyboardButton("✅ Закрытие заказа", callback_data=f"executor_complete_order_{order_id}")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

@check_state(required_state="executor_idle")
async def handle_executor_set_montage_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик кнопки "📅 Дата выполнения" для исполнителя.
    Переход в режим "ввода даты выполнения".
    """
    query = update.callback_query
    callback_data = query.data
    order_id = int(callback_data.split("_")[-1])
    user_id = update.effective_user.id
    logging.info(f"[EXECUTOR] {user_id} выбрал настройку даты выполнения для заказа {order_id}")

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
        logging.error(f"[EXECUTOR] Заказ {order_id} не найден или не принадлежит пользователю {user_id}")
        await query.answer("❌ Ошибка: заказ не найден.", show_alert=True)
        return

    # Смена состояния
    await update_user_state(user_id, "executor_date_input")
    logging.info(f"[EXECUTOR] Состояние пользователя {user_id} изменено на 'executor_date_input'")

    # Отправляем сообщение с текущими данными о заказе
    await query.answer("Переключаемся в режим ввода даты выполнения.", show_alert=False)
    montage_date = order["montage_date"] or "Не назначена"
    await query.message.reply_text(
        f"📋 *Текущее задание №{order_id}*\n"
        f"🏠 *Адрес клиента:* {order['customer_address']}\n"
        f"📞 *Телефон клиента:* {order['customer_phone']}\n"
        f"📅 *Дата выполнения:* {montage_date}\n"
        "\nВведите новую дату выполнения в формате: *YYYY-MM-DD*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["⬅️ Возврат в меню"]], resize_keyboard=True)
    )
@check_state("executor_date_input")
async def handle_executor_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает ввод даты выполнения от исполнителя.
    """
    user_id = update.effective_user.id
    order_id = context.user_data.get("order_id")  # ID заказа сохраняется в user_data при выборе "Дата выполнения"
    input_text = update.message.text.strip()

    logging.info(f"[EXECUTOR] Пользователь {user_id} вводит дату выполнения для заказа {order_id}: '{input_text}'")

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
        f"Вы уверены, что хотите сохранить дату выполнения: *{montage_date.strftime('%Y-%m-%d')}*?"
    )
    confirm_buttons = [
        [
            InlineKeyboardButton("✅ Да", callback_data=f"executor_confirm_date_input_{order_id}"),
            InlineKeyboardButton("❌ Нет", callback_data=f"executor_cancel_date_input_{order_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(confirm_buttons)

    await update.message.reply_text(
        confirm_message,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    logging.info(f"✅ Введена дата {montage_date} для заказа {order_id}, ожидается подтверждение.")

@check_state(required_state="executor_date_input")
async def handle_executor_date_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает подтверждение сохранения даты выполнения от исполнителя.
    """
    query = update.callback_query
    callback_data = query.data
    user_id = update.effective_user.id
    order_id = context.user_data.get("order_id")
    montage_date = context.user_data.get("montage_date")

    logging.info(f"[EXECUTOR] Пользователь {user_id} нажал подтверждение: {callback_data}.")

    # Проверяем наличие необходимых данных
    if not order_id or not montage_date:
        logging.error(f"[EXECUTOR] order_id или montage_date отсутствуют для пользователя {user_id}.")
        await query.answer("❌ Ошибка: данные заказа или дата отсутствуют. Попробуйте заново.", show_alert=True)
        return

    # Обрабатываем подтверждение
    if callback_data == f"executor_confirm_date_input_{order_id}":
        # Сохраняем дату выполнения в БД
        try:
            with db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE orders SET montage_date = %s WHERE id = %s",
                    (montage_date, order_id)
                )
                conn.commit()

            logging.info(f"✅ Дата выполнения {montage_date} сохранена в БД для заказа {order_id}.")
            await query.answer("✅ Дата выполнения успешно сохранена.", show_alert=False)

            # Отправляем сообщение пользователю
            await query.edit_message_text(
                f"✅ Дата выполнения *{montage_date}* успешно сохранена для заказа №{order_id}.",
                parse_mode="Markdown"
            )

            # Возвращаем пользователя к списку задач
            await update_user_state(user_id, "executor_idle")
            await handle_executor_current_tasks(update, context)

        except Exception as e:
            logging.error(f"❌ Ошибка сохранения даты выполнения для заказа {order_id}: {e}")
            await query.answer("❌ Ошибка сохранения даты. Попробуйте снова.", show_alert=True)

    elif callback_data == f"executor_cancel_date_input_{order_id}":
        # Пользователь отменил сохранение
        logging.info(f"[EXECUTOR] Пользователь {user_id} отменил сохранение даты для заказа {order_id}.")
        await query.answer("❌ Изменение даты отменено.", show_alert=False)

        # Возвращаем пользователя в режим ввода даты
        await update_user_state(user_id, "executor_date_input")
        await query.message.reply_text(
            "Введите новую дату выполнения в формате YYYY-MM-DD или нажмите 'Назад в заказы'.",
            reply_markup=ReplyKeyboardMarkup([["⬅️ Возврат в меню"]], resize_keyboard=True)
        )

    else:
        logging.warning(f"[EXECUTOR] Неизвестное действие: {callback_data} для пользователя {user_id}.")
        await query.answer("❌ Неизвестное действие. Попробуйте снова.", show_alert=True)

@check_state(required_state="executor_date_input")
async def handle_executor_cancel_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает нажатие кнопки "Назад в заказы".
    Возвращает пользователя к списку текущих задач.
    """
    query = update.callback_query
    user_id = update.effective_user.id

    logging.info(f"[EXECUTOR] Пользователь {user_id} нажал кнопку 'Назад в заказы'.")

    # Меняем состояние пользователя на просмотр задач
    await update_user_state(user_id, "executor_idle")
    logging.info(f"[EXECUTOR] Состояние пользователя {user_id} изменено на 'executor_idle'.")

    # Уведомляем пользователя, что он возвращен к задачам
    await query.answer("Возвращаемся к списку заданий.", show_alert=False)

    # Вызываем функцию отображения списка текущих задач
    await handle_executor_current_tasks(update, context)


async def handle_executor_return_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает нажатие кнопки "⬅️ Возврат в меню".
    Перенаправляет пользователя в список новых заданий.
    """
    user_id = update.effective_user.id
    logging.info(f"[EXECUTOR] Пользователь {user_id} вернулся в меню.")

    # Обновляем состояние пользователя на стандартное
    await update_user_state(user_id, "executor_idle")

    # Отправляем список новых заданий
    await handle_executor_new_tasks(update, context)


@check_state(required_state="executor_idle")
async def handle_executor_complete_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает нажатие кнопки "✅ Закрытие заказа".
    Проверяет возможность завершения заказа и предлагает подтвердить завершение.
    """
    query = update.callback_query
    callback_data = query.data
    order_id = int(callback_data.split("_")[-1])
    user_id = update.effective_user.id

    logging.info(f"[EXECUTOR] Пользователь {user_id} нажал 'Закрытие заказа' для заказа {order_id}.")

    # Получаем данные о заказе
    with db_connect() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT 
                o.customer_address, 
                c.phone AS customer_phone, 
                o.montage_date, 
                o.description,
                o.deadline_at,
                o.status
            FROM 
                orders o
            JOIN 
                customers c ON o.customer_id = c.id
            WHERE 
                o.id = %s AND o.installer_id = (SELECT id FROM users WHERE telegram_id = %s)
        """, (order_id, user_id))
        order = cursor.fetchone()

    # 1️⃣ Ошибка: заказ не найден или принадлежит другому пользователю
    if not order:
        logging.error(f"[EXECUTOR] Заказ {order_id} не найден или не принадлежит пользователю {user_id}.")
        await query.answer("❌ Ошибка: заказ не найден.", show_alert=True)

        # Сообщение пользователю
        await query.message.reply_text(
            f"❌ Ошибка: задание №{order_id} не найдено в базе или не принадлежит вам.\n"
            "Пожалуйста, обновите список заданий и попробуйте снова.",
            parse_mode="Markdown"
        )
        return

    # 2️⃣ Ошибка: заказ уже закрыт
    if order["status"] == "Завершен":
        logging.warning(f"[EXECUTOR] Попытка закрыть уже завершенный заказ {order_id}.")
        await query.answer("⚠️ Этот заказ уже закрыт.", show_alert=True)

        # Сообщение пользователю
        await query.message.reply_text(
            f"⚠️ Задание №{order_id} уже завершено. Повторное закрытие невозможно.\n"
            "Пожалуйста, обновите список заданий.",
            parse_mode="Markdown"
        )
        return

    # 3️⃣ Ошибка: у заказа нет даты выполнения
    if not order["montage_date"]:
        logging.warning(f"[EXECUTOR] У заказа {order_id} нет даты выполнения. Закрытие невозможно.")
        await query.answer("❌ Ошибка: сначала укажите дату выполнения заказа.", show_alert=True)

        # Сообщение пользователю
        await query.message.reply_text(
            f"❌ Невозможно завершить задание №{order_id}, так как не указана дата выполнения.\n"
            "Пожалуйста, сначала установите дату выполнения, затем попробуйте снова.",
            parse_mode="Markdown"
        )
        return

    # ✅ Если нет ошибок, формируем сообщение с деталями заказа
    message = f"""
📋 *Текущее задание №{order_id}*
🏠 *Адрес клиента:* {order['customer_address']}
📞 *Телефон клиента:* {order['customer_phone']}
📝 *Описание:* {order['description']}
📅 *Дата выполнения:* {order['montage_date']}
⏰ *Дедлайн:* {order['deadline_at']}
"""
    reply_markup = close_task_executor_buttons(order_id)

    # Отправляем сообщение с кнопками подтверждения
    if update.message:
        await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await query.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)

    logging.info(f"📋 Информация о заказе {order_id} отправлена исполнителю {user_id}.")


def close_task_executor_buttons(order_id):
    """
    Создаёт инлайн-кнопки для подтверждения завершения задания.
    """
    buttons = [
        [InlineKeyboardButton("✅ Подтвердить закрытие", callback_data=f"executor_confirm_complete_{order_id}")],
        [InlineKeyboardButton("❌ Отмена", callback_data=f"executor_cancel_complete_{order_id}")]
    ]
    return InlineKeyboardMarkup(buttons)
