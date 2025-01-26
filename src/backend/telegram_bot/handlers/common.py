import bcrypt
from telegram import Update
from telegram.ext import ContextTypes
from bot_utils.bot_db_utils import db_connect
from handlers.admin.admin_menu import admin_start
from handlers.dispatcher.dispatcher_menu import dispatcher_start
from handlers.executor.executor_menu import executor_start
from handlers.specialist.specialist_menu import specialist_start
from handlers.customer.customer_menu import customer_start
from handlers.blocked.blocked_menu import blocked_start
from handlers.guest.guest_menu import start_guest
import logging
from dictionaries.text_actions import TEXT_ACTIONS
from dictionaries.callback_actions import CALLBACK_ACTIONS  # Словарь callback_data и функций
from dictionaries.smart_replies import get_smart_reply

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')

# Обработчик команды /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start. Приветствует пользователя в зависимости от его роли.
    """
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    context.user_data['telegram_id'] = user_id

    # Проверяем роль пользователя
    role = context.user_data.get('role')
    if not role:
        # Если роли нет в кеше, запрашиваем её из базы
        role = await get_user_role(user_id)
        context.user_data['role'] = role

    if role == "guest":
        # Гость зарегистрирован, но ждёт активации
        await update.message.reply_text(
            f"Привет, {user_name}!\n"
            "Вы успешно зарегистрированы в системе, но ваша роль пока не активирована.\n"
            "Ожидайте назначения роли администратором."
        )
    elif role is None:
        # Новый пользователь — перенаправляем на стартовую страницу гостя
        await start_guest(update, context)
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
        # Если роль не определена
        await update.message.reply_text(
            f"Добро пожаловать, {user_name}!\n"
            f"Ваша роль: {role}.\n"
            "Что вы хотите сделать?"
        )



# Функция определения роли пользователя
async def get_user_role(user_id: int) -> str | None:
    """
    Проверяет роль пользователя по его telegram_id.
    Возвращает строку с ролью или None, если пользователь отсутствует в базе.
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
                return None  # Явно указываем, что пользователь отсутствует
    except Exception as e:
        logging.error(f"Ошибка подключения к базе данных: {e}")
        return None  # В случае ошибки считаем, что пользователя нет
    finally:
        conn.close()  # Закрываем соединение

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

    # Проверяем наличие callback_data в словаре
    action = CALLBACK_ACTIONS.get(callback_data)
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
