from telegram import Update
from telegram.ext import ContextTypes, CallbackContext, CallbackQueryHandler
from bot_utils.bot_db_utils import db_connect  # Подключение к базе данных
from .keyboards.common_keyboards import guest_keyboard
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')


# Обработчик команды /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start. Приветствует пользователя в зависимости от его роли.
    """
    user_id = update.effective_user.id  # Получаем ID пользователя
    user_name = update.effective_user.first_name  # Получаем имя пользователя

    # Проверяем кешированную роль
    role = context.user_data.get('role')

    if not role:
        # Если роли нет в кеше, запрашиваем из базы
        role = await get_user_role(user_id)
        context.user_data['role'] = role  # Сохраняем роль в кеш

    if role == "guest":
        # Если роль "гость", начинаем запрос имени
        await update.message.reply_text(
            f"Привет, {user_name}!\n"
            "Мы не нашли вас в системе. Пожалуйста, введите своё имя для идентификации."
        )
        context.user_data['registration_step'] = "name_request"  # Устанавливаем шаг регистрации
    else:
        # Если пользователь найден, приветствуем в зависимости от роли
        await update.message.reply_text(
            f"Добро пожаловать, {user_name}!\n"
            f"Ваша роль: {role}.\n"
            "Что вы хотите сделать?"
        )

async def process_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Универсальный обработчик для управления регистрацией.
    Направляет сообщения в зависимости от этапа регистрации.
    """
    registration_step = context.user_data.get("registration_step")

    if registration_step == "name_request":
        # Перенаправляем в обработчик process_name
        await process_name(update, context)
    elif registration_step == "email_request":
        # Перенаправляем в обработчик process_email
        await process_email(update, context)
    elif registration_step == "admin_message":
        # Перенаправляем в обработчик process_admin_message
        await process_admin_message(update, context)
    else:
        # Если шаг регистрации не установлен, отправляем предупреждение
        await update.message.reply_text(
            "Произошла ошибка. Попробуйте снова отправить команду /start."
        )




# Обработчик текстового сообщения для проверки имени пользователя
async def process_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик текстового сообщения. Проверяет введённое имя пользователя.
    """
    # Проверяем текущий шаг регистрации
    if context.user_data.get('registration_step') != "name_request":
        return

    user_name = update.message.text  # Получаем введённое имя пользователя
    user_id = update.effective_user.id  # Получаем telegram_id пользователя

    logging.info(f"Проверка имени '{user_name}' для пользователя {user_id}...")

    # Проверяем имя в базе данных
    user_data = await check_user_name_in_db(user_name)

    if user_data:
        logging.info(f"Имя '{user_name}' найдено. ID пользователя: {user_data['id']}, роль: {user_data['role']}")

        # Если имя найдено, привязываем telegram_id и сохраняем данные
        await bind_telegram_id_to_user(user_id, user_data['id'])

        # Сохраняем роль в кеш
        role = user_data['role']
        context.user_data['role'] = role

        # Приветствуем пользователя
        await update.message.reply_text(
            f"Добро пожаловать, {user_name}!\n"
            f"Ваша роль: {role}.\n"
            "Что вы хотите сделать?"
        )
        # Завершаем процесс регистрации
        context.user_data.pop('registration_step', None)
    else:
        logging.info(f"Имя '{user_name}' не найдено в базе данных.")

        # Если имя не найдено, запрашиваем email
        await update.message.reply_text(
            "Имя не найдено. Пожалуйста, введите ваш email для идентификации."
        )
        context.user_data['registration_step'] = "email_request"  # Устанавливаем шаг регистрации


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


# Обработчик ввода email
async def process_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик ввода email. Проверяет email в базе данных и завершает регистрацию.
    """
    # Проверяем текущий шаг регистрации
    if context.user_data.get('registration_step') != "email_request":
        return

    email = update.message.text.strip()  # Получаем текст сообщения
    user_id = update.effective_user.id

    logging.info(f"Проверка email '{email}' для пользователя {user_id}...")

    # Проверяем email в базе данных
    user = find_user_by_email(email)

    if user:
        logging.info(f"Email '{email}' найден. ID пользователя: {user['id']}, роль: {user['role']}")

        # Привязываем telegram_id к пользователю
        update_user_telegram_id(user['id'], user_id)
        role = user['role']  # Получаем роль пользователя
        context.user_data['role'] = role  # Сохраняем роль в кеш

        # Приветствие для найденного пользователя
        await update.message.reply_text(
            f"Добро пожаловать, {user['name']}!\n"
            f"Ваша роль: {role}.\n"
            "Что вы хотите сделать?"
        )
        # Убираем шаг регистрации
        context.user_data.pop('registration_step', None)
    else:
        logging.info(f"Email '{email}' не найден в базе данных.")

        # Email не найден
        await update.message.reply_text(
            "Email не найден. Пожалуйста, выберите следующее действие:",
            reply_markup=generate_email_error_keyboard()  # Показываем инлайн-кнопки
        )

# Генерация Inline-клавиатуры
def generate_email_error_keyboard():
    """
    Возвращает Inline-клавиатуру для выбора действий при неверном email.
    """
    keyboard = [
        [InlineKeyboardButton("🔁 Повторить ввод имени", callback_data="repeat_name")],
        [InlineKeyboardButton("✍️ Зарегистрироваться", callback_data="register_user")],
        [InlineKeyboardButton("📞 Связаться с администратором", callback_data="contact_admin")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Генерация Inline-клавиатуры для сообщения администратора
def generate_admin_message_keyboard():
    """
    Возвращает Inline-клавиатуру с кнопкой '⬅️ Вернуться к выбору действия'.
    """
    keyboard = [
        [InlineKeyboardButton("⬅️ Вернуться к выбору действия", callback_data="return_to_action")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Обработчик ввода сообщения для администратора
async def process_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает сообщение, введённое пользователем для администратора.
    """
    # Проверяем текущий шаг регистрации
    if context.user_data.get('registration_step') != "admin_message":
        return

    # Получаем сообщение пользователя
    admin_message = update.message.text.strip()
    user_name = update.effective_user.full_name
    user_id = update.effective_user.id

    # Логируем сообщение
    logging.info(f"Сообщение от пользователя {user_name} ({user_id}): {admin_message}")

    # Сохраняем сообщение и отправляем администраторам
    success = await send_message_to_admins(context, user_name, user_id, admin_message)

    if success:
        # Подтверждаем отправку сообщения
        await update.message.reply_text(
            "Ваше сообщение успешно отправлено администраторам. Ожидайте ответа."
        )
        # Убираем шаг регистрации
        context.user_data.pop('registration_step', None)
    else:
        # Уведомляем об ошибке
        await update.message.reply_text(
            "К сожалению, произошла ошибка при отправке сообщения администраторам. Попробуйте позже."
        )

async def send_message_to_admins(context: ContextTypes.DEFAULT_TYPE, user_name: str, user_id: int, admin_message: str) -> bool:
    """
    Отправляет сообщение от пользователя всем администраторам.
    Возвращает True при успешной отправке, иначе False.
    """
    try:
        # Получаем список telegram_id администраторов
        conn = db_connect()
        with conn.cursor() as cursor:
            query = """
                SELECT telegram_id FROM users
                WHERE role = (SELECT id FROM roles WHERE name = 'admin')
            """
            cursor.execute(query)
            admins = cursor.fetchall()

        if not admins:
            logging.warning("Администраторы не найдены в базе данных.")
            return False

        # Формируем сообщение
        message = (
            f"Пользователь {user_name} (ID: {user_id}) оставил сообщение:\n"
            f"\"{admin_message}\""
        )

        # Отправляем сообщение каждому администратору
        for admin in admins:
            admin_id = admin['telegram_id']
            if admin_id:  # Проверяем, что telegram_id не пустой
                await context.bot.send_message(chat_id=admin_id, text=message)

        logging.info(f"Сообщение успешно отправлено {len(admins)} администраторам.")
        return True
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения администраторам: {e}")
        return False




# Обновление обработчика нажатий кнопок
async def handle_inline_buttons(update: Update, context: CallbackContext):
    """
    Обрабатывает нажатия на Inline-кнопки из клавиатуры.
    """
    query = update.callback_query
    await query.answer()  # Отвечаем на нажатие кнопки

    if query.data == "repeat_name":
        # Возвращаем пользователя к шагу ввода имени
        context.user_data['registration_step'] = "name_request"
        await query.edit_message_text(
            text="Введите ваше имя для идентификации."
        )

    elif query.data == "register_user":
        # Переводим пользователя в процедуру регистрации
        context.user_data['registration_step'] = "start_registration"
        await query.edit_message_text(
            text="Пожалуйста, введите своё имя для регистрации."
        )

    elif query.data == "contact_admin":
        # Переводим пользователя в шаг ввода сообщения для администратора
        context.user_data['registration_step'] = "admin_message"
        await query.edit_message_text(
            text="Напишите, что именно вы хотите сообщить администратору.",
            reply_markup=generate_admin_message_keyboard()  # Показываем кнопку "⬅️ Вернуться к выбору действия"
        )

    elif query.data == "return_to_action":
        # Возвращаем пользователя на этап выбора действия
        context.user_data['registration_step'] = "email_request"
        await query.edit_message_text(
            text="Email не найден. Пожалуйста, выберите следующее действие:",
            reply_markup=generate_email_error_keyboard()  # Показываем клавиатуру с основными кнопками
        )


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



# Функция определения роли пользователя
async def get_user_role(user_id: int) -> str:
    """
    Проверяет роль пользователя по его telegram_id.
    Возвращает строку с ролью: "guest" или роль из базы данных.
    """
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
            return result['role'] if result else "guest"
    except Exception as e:
        # Логируем ошибку подключения
        print(f"Ошибка подключения к базе данных: {e}")
        return "guest"
    finally:
        conn.close()  # Закрываем соединение


# Обработчик кнопки "Помощь"
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды для кнопки "Помощь".
    """
    await update.message.reply_text(
        "Я здесь, чтобы помочь! Вот список доступных действий:\n"
        "1. Нажмите '✍️ Регистрация', чтобы зарегистрироваться в системе.\n"
        "2. Нажмите '🆘 Помощь', чтобы получить информацию.\n\n"
        "Если у вас возникли вопросы, обратитесь к администратору."
    )
