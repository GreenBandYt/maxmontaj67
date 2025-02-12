import bcrypt
import logging
from telegram import Update
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
from telegram_bot.dictionaries.states import INITIAL_STATES

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start. Устанавливает начальное состояние согласно INITIAL_STATES.
    """
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    context.user_data['telegram_id'] = user_id

    # Получаем роль и состояние пользователя из БД
    role_data = await get_user_role_and_state(user_id)
    role = role_data.get("role", "new_guest")
    current_state = role_data.get("state", "")

    # Определяем начальное состояние для роли
    expected_state = INITIAL_STATES.get(role, "guest_idle")

    # Если состояние в БД не соответствует ожидаемому, обновляем его
    if current_state != expected_state:
        logging.info(f"Сброс состояния для user_id {user_id}: {current_state} -> {expected_state}")
        try:
            with db_connect() as conn:
                cursor = conn.cursor()
                query = "UPDATE users SET state = %s WHERE telegram_id = %s"
                cursor.execute(query, (expected_state, user_id))
                conn.commit()
        except Exception as e:
            logging.error(f"Ошибка обновления состояния в БД: {e}")
            return

    # Обновляем локальный контекст
    context.user_data['role'] = role
    context.user_data['state'] = expected_state

    await update.message.reply_text(f"⚙️ [На время разработки]\nРоль: {role}\nСостояние: {expected_state}\n")

    # Вызываем обработчики для ролей
    role_handlers = {
        "new_guest": start_guest,
        "guest": lambda u, c: u.message.reply_text(
            f"Привет, {user_name}! Вы зарегистрированы, но ваша роль пока не активирована."
        ),
        "admin": admin_start,
        "dispatcher": dispatcher_start,
        "executor": executor_start,
        "specialist": specialist_start,
        "customer": customer_start,
        "blocked": blocked_start,
    }

    if role in role_handlers:
        await role_handlers[role](update, context)
    else:
        await update.message.reply_text(f"Добро пожаловать, {user_name}!\nВаша роль: {role}.")

async def get_user_role_and_state(user_id: int) -> dict:
    """
    Возвращает роль и состояние пользователя из базы данных.
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            query = """
                SELECT r.name AS role, u.state AS state
                FROM users u
                JOIN roles r ON u.role = r.id
                WHERE u.telegram_id = %s
            """
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            if result:
                return {"role": result[0], "state": result[1]}
            else:
                return {"role": "new_guest", "state": INITIAL_STATES.get("new_guest", "guest_idle")}
    except Exception as e:
        logging.error(f"Ошибка при получении данных пользователя: {e}")
        return {"role": "new_guest", "state": INITIAL_STATES.get("new_guest", "guest_idle")}

async def get_user_state_from_db(user_id: int) -> str:
    """
    Получает текущее состояние пользователя из базы данных.
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            query = "SELECT state FROM users WHERE telegram_id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                logging.warning(f"Пользователь с ID {user_id} не найден в БД.")
                return None
    except Exception as e:
        logging.error(f"Ошибка получения состояния из БД: {e}")
        return None

async def handle_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для пользовательских текстовых сообщений.
    """
    user_id = update.message.from_user.id
    user_state = await get_user_state_from_db(user_id)

    if not user_state or user_state not in INITIAL_STATES.values():
        logging.warning(f"⚠ Некорректное состояние '{user_state}' для пользователя {user_id}.")
        await update.message.reply_text("Ваш запрос не может быть обработан.")
        return

    user_text = update.message.text.strip()

    action = TEXT_ACTIONS.get(user_text)
    if action:
        await action(update, context)
        return

    response = get_smart_reply(user_text)
    if response:
        await update.message.reply_text(response)
        return

    await update.message.reply_text("Извините, я вас не понял. Попробуйте уточнить запрос.")

async def handle_inline_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик инлайн-кнопок.
    """
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    action = CALLBACK_ACTIONS.get(callback_data)

    if action:
        await action(update, context)
    else:
        await query.edit_message_text("Кнопка больше не активна.")
