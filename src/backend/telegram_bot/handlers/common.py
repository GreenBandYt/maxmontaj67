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

from handlers.executor.executor_menu import (
    handle_executor_accept_order,
    handle_executor_decline_order,
)
from handlers.specialist.specialist_menu import (
    handle_specialist_accept_order,
    handle_specialist_decline_order,
)

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start. Приветствует пользователя, устанавливая состояние согласно INITIAL_STATES для его роли.
    Независимо от того, что хранится в базе, состояние будет сброшено до начального значения для данной роли.
    """
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    context.user_data['telegram_id'] = user_id

    # Получаем роль и состояние пользователя из БД
    role_data = await get_user_role_and_state(user_id)
    role = role_data.get("role", "new_guest")
    current_state = role_data.get("state", "")

    # Определяем ожидаемое начальное состояние для полученной роли согласно словарю INITIAL_STATES
    expected_state = INITIAL_STATES.get(role, "guest_idle")

    # Если состояние в базе не соответствует ожидаемому, сбрасываем его в БД
    if current_state != expected_state:
        logging.info(f"Сброс состояния для user_id {user_id}: {current_state} -> {expected_state}")
        try:
            conn = db_connect()
            with conn.cursor() as cursor:
                query = "UPDATE users SET state = %s WHERE telegram_id = %s"
                cursor.execute(query, (expected_state, user_id))
            conn.commit()
        except Exception as e:
            logging.error(f"Ошибка обновления состояния в БД: {e}")
        finally:
            if conn:
                conn.close()
        current_state = expected_state  # локально обновляем состояние

    # Сохраняем актуальные данные в context.user_data
    context.user_data['role'] = role
    context.user_data['state'] = current_state

    # Выводим отладочную информацию пользователю
    await update.message.reply_text(
        f"⚙️ [На время разработки]\n"
        f"Роль: {role}\n"
        f"Состояние: {current_state}\n"
    )

    # В зависимости от роли вызываем соответствующий обработчик
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
            f"Состояние: {current_state}\n"
            "Что вы хотите сделать?"
        )


async def get_user_role_and_state(user_id: int) -> dict:
    """
    Проверяет роль и состояние пользователя по его telegram_id.
    Возвращает словарь с ключами 'role' и 'state'.
    Если пользователь не найден, возвращает {'role': 'new_guest', 'state': INITIAL_STATES.get('new_guest', 'guest_idle')}.
    """
    logging.info(f"Проверка роли и состояния для user_id: {user_id}")
    try:
        conn = db_connect()  # Устанавливаем подключение к базе данных
        with conn.cursor() as cursor:
            query = """
                SELECT r.name AS role, u.state AS state
                FROM users u
                JOIN roles r ON u.role = r.id
                WHERE u.telegram_id = %s
            """
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            if result:
                try:
                    # Если драйвер возвращает словарь:
                    role_value = result["role"]
                    state_value = result["state"]
                except (TypeError, KeyError):
                    # Если результат – кортеж
                    role_value = result[0]
                    state_value = result[1]
                logging.info(f"Получено: роль = {role_value}, состояние = {state_value}")
                return {"role": role_value, "state": state_value}
            else:
                logging.warning(f"Пользователь с user_id {user_id} не найден в базе.")
                return {"role": "new_guest", "state": INITIAL_STATES.get("new_guest", "guest_idle")}
    except Exception as e:
        logging.error(f"Ошибка при получении роли и состояния: {e}")
        return {"role": "new_guest", "state": INITIAL_STATES.get("new_guest", "guest_idle")}
    finally:
        if conn:
            conn.close()



# Функция определения роли пользователя
async def get_user_role(user_id: int) -> str:
    """
    Проверяет роль пользователя по его telegram_id.
    Возвращает строку с ролью или 'new_guest', если пользователь отсутствует в базе.
    """
    logging.info(f"Проверка роли для user_id: {user_id}")
    try:
        conn = db_connect()  # Устанавливаем подключение к базе данных
        with conn.cursor() as cursor:
            query = """
                SELECT r.name AS role
                FROM users u
                JOIN roles r ON u.role = r.id
                WHERE u.telegram_id = %s
            """
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            if result:
                logging.info(f"Роль для user_id {user_id}: {result['role']}")
                return result['role']
            else:
                logging.warning(f"Пользователь с user_id {user_id} не найден в базе.")
                return "new_guest"  # Если пользователь не найден, назначаем роль new_guest
    except Exception as e:
        logging.error(f"Ошибка подключения к базе данных: {e}")
        return "new_guest"  # В случае ошибки возвращаем 'new_guest'
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
    """
    Универсальный обработчик для обработки текста от пользователя.
    """
    # Получаем текущее состояние пользователя
    user_state = context.user_data.get("state", None)

    # Если пользователь находится в состоянии, отличном от начального, завершаем обработчик
    if user_state and user_state not in INITIAL_STATES.values():
        logging.warning(
            f"⚠ Попытка доступа к универсальному обработчику из состояния '{user_state}' "
            f"(роль: {context.user_data.get('role', 'unknown')})."
        )
        return  # Завершаем обработчик, так как состояние требует специфической обработки

    # Получаем текст сообщения от пользователя
    user_text = update.message.text.strip()

    # Проверяем, является ли текст кнопкой
    action = TEXT_ACTIONS.get(user_text)
    if action:
        await action(update, context)  # Вызываем функцию напрямую
        return

    # Проверяем "умные ответы"
    response = get_smart_reply(user_text)
    if response:
        await update.message.reply_text(response)
        return

    # Если ничего не найдено, отправляем сообщение по умолчанию
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
