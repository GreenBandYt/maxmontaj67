# src/backend/telegram_bot/handlers/common.py

import bcrypt
import logging
from telegram import Update
import pymysql
from telegram.ext import ContextTypes
from telegram_bot.bot_utils.bot_db_utils import db_connect
from telegram_bot.handlers.admin.admin_menu import admin_start
from telegram_bot.handlers.dispatcher.dispatcher_menu import dispatcher_start
from telegram_bot.handlers.executor.executor_menu import executor_start
from telegram_bot.handlers.specialist.specialist_menu import specialist_start
from telegram_bot.handlers.customer.customer_menu import customer_start
from telegram_bot.handlers.blocked.blocked_menu import blocked_start
from telegram_bot.handlers.guest.guest_menu import start_guest
from telegram_bot.dictionaries.text_actions import TEXT_ACTIONS
from telegram_bot.dictionaries.callback_actions import CALLBACK_ACTIONS
from telegram_bot.dictionaries.smart_replies import get_smart_reply
from telegram_bot.dictionaries.states import INITIAL_STATES, STATE_HANDLERS

from telegram_bot.bot_utils.access_control import check_access, check_state
from telegram_bot.bot_utils.db_utils import update_user_state, get_user_state
from telegram_bot.bot_utils.admin_messaging import (
    send_message_to_admins,process_admin_message,  handle_reply_button,
    handle_reply_button, handle_reply_message,
)


from handlers.executor.executor_menu import (
    handle_executor_accept_order,
    handle_executor_decline_order,
    handle_executor_set_montage_date,
    handle_executor_date_input,
    handle_executor_date_confirm,
    handle_executor_cancel_date_input,
    handle_executor_return_to_menu,
    handle_executor_complete_order,
)

from handlers.specialist.specialist_menu import (
    handle_specialist_accept_order,
    handle_specialist_decline_order,
    handle_specialist_set_montage_date,
    handle_specialist_date_input,
    handle_specialist_date_confirm,
    handle_specialist_cancel_date_input,
    handle_specialist_return_to_menu,
    handle_specialist_complete_order,
)


# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')

# Обработчик команды /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start. Приветствует пользователя в зависимости от его роли
    и устанавливает начальное состояние.
    """
    user_id = update.effective_user.id  # Telegram ID пользователя
    user_name = update.effective_user.first_name

    try:
        conn = db_connect()
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # Проверяем роль и состояние пользователя
            query = """
                SELECT r.name AS role, u.user_state
                FROM users u
                JOIN roles r ON u.role = r.id
                WHERE u.telegram_id = %s
            """
            cursor.execute(query, (user_id,))
            user_data = cursor.fetchone()

            if not user_data:
                # Если пользователь не найден, создаем нового гостя
                role = "new_guest"
                initial_state = "guest_idle"
                cursor.execute("""
                    INSERT INTO users (telegram_id, name, role, user_state)
                    VALUES (%s, %s, (SELECT id FROM roles WHERE name = 'guest'), %s)
                """, (user_id, user_name, initial_state))
                conn.commit()
            else:
                role = user_data["role"]
                initial_state = INITIAL_STATES.get(role, "guest_idle")

                # Обновляем состояние в базе данных
                cursor.execute("""
                    UPDATE users
                    SET user_state = %s
                    WHERE telegram_id = %s
                """, (initial_state, user_id))
                conn.commit()

        # Устанавливаем начальное состояние и обрабатываем роль
        if role == "new_guest":
            await start_guest(update, context)
        elif role == "guest":
            await update.message.reply_text(
                f"Привет, {user_name}!\n"
                "Вы успешно зарегистрированы в системе, но ваша роль пока не активирована.\n"
                "Ожидайте назначения роли администратором."
            )
        elif role == "admin":
            await admin_start(update, context)
        elif role == "dispatcher":
            await dispatcher_start(update, context)
        elif role == "executor":
            await executor_start(update, context)
        elif role == "specialist":
            await specialist_start(update, context)
        elif role == "customer":
            await customer_start(update, context)
        elif role == "blocked":
            await blocked_start(update, context)
        else:
            await update.message.reply_text(
                f"Добро пожаловать, {user_name}!\n"
                f"Ваша роль: {role}.\n"
                "Что вы хотите сделать?"
            )

    except Exception as e:
        logging.error(f"Ошибка при обработке команды /start: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте снова позже.")
    finally:
        if conn:
            conn.close()


# Функция для проверки имени в базе данных
async def check_user_name_in_db(user_name: str) -> dict:
    """
    Проверяет имя пользователя в базе данных.
    Возвращает словарь с данными пользователя, если найден, иначе None.
    """
    try:
        conn = db_connect()  # Устанавливаем подключение к базе данных
        with conn.cursor() as cursor:
            query = """
                SELECT u.id, u.role, r.name AS role_name
                FROM users u
                JOIN roles r ON u.role = r.id
                WHERE u.name = %s
            """
            cursor.execute(query, (user_name,))
            result = cursor.fetchone()
            if result:
                print(f"[INFO] Имя '{user_name}' найдено в базе данных.")
                return {
                    "id": result['id'],
                    "role": result['role_name']
                }
            else:
                print(f"[INFO] Имя '{user_name}' не найдено в базе данных.")
                return None
    except Exception as e:
        print(f"[ERROR] Ошибка при проверке имени в базе данных: {e}")
        return None
    finally:
        conn.close()  # Закрываем соединение

# Функция для привязки telegram_id к пользователю
async def bind_telegram_id_to_user(telegram_id: int, user_id: int):
    """
    Привязывает telegram_id к пользователю в базе данных.
    """
    try:
        conn = db_connect()  # Устанавливаем подключение к базе данных
        with conn.cursor() as cursor:
            query = "UPDATE users SET telegram_id = %s WHERE id = %s"
            cursor.execute(query, (telegram_id, user_id))
        conn.commit()  # Сохраняем изменения
    except Exception as e:
        # Логируем ошибку подключения
        print(f"Ошибка при привязке telegram_id к пользователю: {e}")
    finally:
        conn.close()  # Закрываем соединение

# Функция для поиска пользователя по email
def find_user_by_email(email: str):
    """
    Ищет пользователя по email в базе данных.
    """
    conn = db_connect()  # Устанавливаем подключение
    try:
        with conn.cursor() as cursor:
            query = """
                SELECT u.id, u.name, r.name AS role
                FROM users u
                JOIN roles r ON u.role = r.id
                WHERE u.email = %s
            """
            cursor.execute(query, (email,))
            result = cursor.fetchone()
            if result:
                print(f"[INFO] Email '{email}' найден в базе данных.")
                return result
            else:
                print(f"[INFO] Email '{email}' не найден в базе данных.")
                return None
    except Exception as e:
        print(f"[ERROR] Ошибка при поиске email в базе данных: {e}")
        return None
    finally:
        conn.close()

# Функция для обновления telegram_id в базе данных
def update_user_telegram_id(user_id: int, telegram_id: int):
    """
    Привязывает telegram_id к существующему пользователю.
    """
    conn = db_connect()  # Устанавливаем подключение
    try:
        with conn.cursor() as cursor:
            query = """
                UPDATE users
                SET telegram_id = %s
                WHERE id = %s
            """
            cursor.execute(query, (telegram_id, user_id))
            conn.commit()  # Подтверждаем изменения
    finally:
        conn.close()


async def handle_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("🛠️ Вызван универсальный обработчик handle_user_input")
    """
    Универсальный обработчик для обработки текста от пользователя.
    """
    user_id = update.effective_user.id  # Получаем user_id из update
    user_state = await get_user_state(user_id)  # Получаем текущее состояние пользователя

    # Проверяем, зарегистрирован ли обработчик для текущего состояния
    if user_state in STATE_HANDLERS:
        handler_name = STATE_HANDLERS[user_state]
        try:
            # Получаем функцию по имени из глобальной области видимости
            handler = globals().get(handler_name)
            if callable(handler):
                logging.info(f"🔍 Состояние пользователя {user_id}: {user_state}. Вызывается обработчик {handler_name}.")
                await handler(update, context)
                return
            else:
                raise ValueError(f"Обработчик {handler_name} не является вызываемой функцией.")
        except Exception as e:
            logging.error(f"❌ Ошибка при вызове обработчика {handler_name} для состояния {user_state}: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке вашего запроса. Пожалуйста, обратитесь к администратору."
            )
            return

    # Если состояние не определено, продолжаем проверку других условий
    logging.warning(f"⚠️ Неизвестное состояние пользователя {user_id}: {user_state}. Проверяем другие условия.")


    # Получаем текст сообщения от пользователя
    user_text = update.message.text.strip()

    # Проверяем, является ли текст кнопкой
    action = TEXT_ACTIONS.get(user_text)
    if action:
        logging.info(f"🔘 Найдено действие для текста '{user_text}': {action.__name__}.")
        await action(update, context)  # Вызываем функцию напрямую
        return

    # Проверяем "умные ответы"
    response = get_smart_reply(user_text)
    if response:
        logging.info(f"🤖 Умный ответ на '{user_text}': {response}.")
        await update.message.reply_text(response)
        return

    # Если ничего не найдено, отправляем сообщение по умолчанию
    logging.info(f"❓ Пользователь {user_id} отправил непонятный текст: '{user_text}'.")
    await update.message.reply_text(
        "Извините, я вас не понял. Попробуйте уточнить запрос или воспользуйтесь кнопками меню. 🤔"
    )

async def handle_inline_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Универсальный обработчик для инлайн-кнопок.
    """
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие кнопки


    callback_data = query.data  # Получаем callback_data кнопки
    logging.info(f"Получено callback_data: {callback_data}")

    # Ищем действие по префиксу callback_data (без ID заказа)
    action = next((v for k, v in CALLBACK_ACTIONS.items() if callback_data.startswith(k)), None)

    if action:
        try:
            # Вызываем функцию напрямую из словаря
            await globals()[action](update, context)
        except KeyError:
            logging.error(f"Функция для callback_data '{callback_data}' не найдена.")
            await query.edit_message_text(
                "Произошла ошибка при выполнении действия. Обратитесь к администратору."
            )
    else:
        # Если callback_data отсутствует в словаре
        logging.warning(f"Неизвестное callback_data: {callback_data}")
        await query.edit_message_text(
            "Кнопка больше не активна. Попробуйте снова или обратитесь к администратору."
        )
