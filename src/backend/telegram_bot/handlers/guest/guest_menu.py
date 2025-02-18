from telegram import Update
from telegram.ext import ContextTypes, CallbackContext
from .guest_keyboards import guest_keyboard, generate_email_error_keyboard, generate_admin_message_keyboard
from telegram_bot.bot_utils.access_control import check_access

import logging

@check_access(required_role="new_guest", required_state="guest_idle")
async def start_guest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Стартовая страница для гостя.
    """
    await update.message.reply_text(
        f"Добро пожаловать, {update.effective_user.first_name}!\n"
        "Вы находитесь в гостевой зоне. Зарегистрируйтесь, чтобы получить доступ к функционалу.",
        reply_markup=guest_keyboard()  # Клавиатура для гостя
    )


async def handle_guest_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка кнопки "✍️ Регистрация".
    """
    await update.message.reply_text("Регистрация начата. Пожалуйста, введите ваше имя.")

@check_access(required_role="guest", required_state="guest_idle")
async def handle_guest_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка кнопки "🆘 Помощь".
    """
    await update.message.reply_text("Гостевая помощь: Вы можете зарегистрироваться или обратиться к администратору.")

async def handle_inline_buttons(update: Update, context: CallbackContext):
    """
    Обрабатывает нажатия на Inline-кнопки.
    """
    query = update.callback_query
    await query.answer()

    if query.data == "repeat_name":
        # Возвращаем пользователя к шагу ввода имени
        context.user_data['registration_step'] = "name_request"
        await query.edit_message_text("Введите ваше имя для идентификации.")
    elif query.data == "register_user":
        # Начинаем процесс регистрации
        context.user_data['registration_step'] = "registration_name"
        await query.edit_message_text("Пожалуйста, введите своё имя для регистрации.")
    elif query.data == "contact_admin":
        # Сообщение для администратора
        context.user_data['registration_step'] = "admin_message"
        await query.edit_message_text(
            "Напишите сообщение для администратора.",
            reply_markup=generate_admin_message_keyboard()
        )
    elif query.data == "return_to_action":
        # Возвращение к выбору действия
        context.user_data['registration_step'] = "email_request"
        await query.edit_message_text(
            "Email не найден. Пожалуйста, выберите следующее действие:",
            reply_markup=generate_email_error_keyboard()
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
    elif registration_step == "registration_name":
        # Обработка этапа регистрации имени
        await process_registration_name(update, context)
    elif registration_step == "registration_password":
        # Обработка этапа регистрации пароля
        await process_registration_password(update, context)
    elif registration_step == "registration_role":
        # Перенаправляем на этап выбора роли (будет реализовано далее)
        await process_registration_role(update, context)
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


async def process_registration_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает ввод имени пользователя на этапе регистрации.
    """
    # Проверяем текущий шаг регистрации
    if context.user_data.get('registration_step') != "registration_name":
        return

    user_name = update.message.text.strip()  # Получаем введённое имя
    logging.info(f"Проверка уникальности имени '{user_name}'...")

    # Проверяем уникальность имени
    if await is_name_taken(user_name):
        logging.info(f"Имя '{user_name}' уже занято.")
        await update.message.reply_text(
            "Имя уже занято. Попробуйте ввести другое."
        )
    else:
        logging.info(f"Имя '{user_name}' свободно.")
        context.user_data['registration_name'] = user_name  # Сохраняем имя
        context.user_data['registration_step'] = "registration_password"  # Переходим на следующий этап
        await update.message.reply_text(
            "Придумайте и введите пароль для регистрации."
        )

async def is_name_taken(name: str) -> bool:
    """
    Проверяет, занято ли имя в базе данных.
    Возвращает True, если имя уже существует, иначе False.
    """
    try:
        conn = db_connect()
        with conn.cursor() as cursor:
            query = "SELECT COUNT(*) FROM users WHERE name = %s"
            cursor.execute(query, (name,))
            result = cursor.fetchone()
            return result['COUNT(*)'] > 0
    except Exception as e:
        logging.error(f"Ошибка при проверке уникальности имени: {e}")
        return True  # Если произошла ошибка, возвращаем, что имя занято
    finally:
        conn.close()

async def process_registration_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает ввод пароля пользователя на этапе регистрации.
    """
    # Проверяем текущий шаг регистрации
    if context.user_data.get('registration_step') != "registration_password":
        return

    password = update.message.text.strip()  # Получаем введённый пароль
    logging.info("Проверка длины пароля...")

    # Проверяем длину пароля
    if len(password) < 6:
        logging.info("Пароль слишком короткий.")
        await update.message.reply_text(
            "Пароль слишком короткий. Введите пароль длиной не менее 6 символов."
        )
    else:
        logging.info("Пароль принят.")
        context.user_data['registration_password'] = password  # Сохраняем пароль
        context.user_data['registration_step'] = "registration_role"  # Переходим на следующий этап
        await update.message.reply_text(
            "Введите вашу желаемую роль (например: заказчик, исполнитель, специалист)."
        )

async def process_registration_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает ввод желаемой роли пользователя на этапе регистрации.
    """
    # Проверяем текущий шаг регистрации
    if context.user_data.get('registration_step') != "registration_role":
        return

    role = update.message.text.strip().lower()  # Получаем введённую роль
    valid_roles = ["заказчик", "исполнитель", "специалист"]  # Список доступных ролей

    logging.info(f"Проверка роли: {role}")

    if role not in valid_roles:
        logging.info("Некорректная роль.")
        await update.message.reply_text(
            f"Роль введена некорректно. Доступные роли: {', '.join(valid_roles)}. Попробуйте снова."
        )
    else:
        logging.info(f"Роль '{role}' принята.")
        context.user_data['registration_role'] = role  # Сохраняем роль
        context.user_data['registration_step'] = None  # Сбрасываем шаг регистрации

        # Сохраняем пользователя в базе данных
        await save_user_to_db(context)

        # Отправляем сообщение администратору
        await notify_admin_about_registration(context)

        # Подтверждаем регистрацию
        await update.message.reply_text(
            "Спасибо за регистрацию! Ваши данные успешно сохранены."
        )

def hash_password(password: str) -> str:
    """
    Генерирует bcrypt-хэш из пароля.
    """
    try:
        # Хэшируем пароль
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        logging.debug(f"[DEBUG] Пароль успешно хэширован: {hashed}")
        return hashed
    except Exception as e:
        logging.error(f"[ERROR] Ошибка при хэшировании пароля: {e}")
        raise Exception("Ошибка при хэшировании пароля. Проверьте входные данные.")

async def save_user_to_db(context: ContextTypes.DEFAULT_TYPE):
    """
    Сохраняет данные пользователя в базу данных.
    """
    name = context.user_data.get('registration_name')  # Получаем имя пользователя
    password = context.user_data.get('registration_password')  # Получаем сырой пароль
    telegram_id = context.user_data.get('telegram_id')  # Получаем telegram_id пользователя

    # Проверяем наличие обязательных данных
    if not all([name, password, telegram_id]):
        logging.error(f"Отсутствуют обязательные данные для сохранения пользователя! "
                      f"name={name}, password={password}, telegram_id={telegram_id}")
        return

    try:
        # Хэшируем пароль
        password_hash = hash_password(password)

        conn = db_connect()  # Подключаемся к базе данных
        with conn.cursor() as cursor:
            query = """
                INSERT INTO users (name, password_hash, role, telegram_id)
                VALUES (%s, %s, (SELECT id FROM roles WHERE name = 'guest'), %s)
            """
            cursor.execute(query, (name, password_hash, telegram_id))
        conn.commit()
        logging.info("Данные пользователя успешно сохранены в базу данных.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных в базу данных: {e}")
    finally:
        conn.close()

async def notify_admin_about_registration(context: ContextTypes.DEFAULT_TYPE):
    """
    Отправляет сообщение администраторам о новом зарегистрированном пользователе.
    """
    name = context.user_data.get('registration_name')
    role = context.user_data.get('registration_role')
    telegram_id = context.user_data.get('telegram_id')

    try:
        conn = db_connect()
        with conn.cursor() as cursor:
            query = """
                SELECT telegram_id FROM users
                WHERE role = (SELECT id FROM roles WHERE name = 'admin')
            """
            cursor.execute(query)
            admins = cursor.fetchall()

        if not admins:
            logging.warning("Администраторы не найдены.")
            return

        # Формируем сообщение
        message = (
            f"Новый пользователь зарегистрирован:\n"
            f"Имя: {name}\n"
            f"Роль: {role}\n"
            f"Telegram ID: {telegram_id}"
        )

        # Отправляем сообщение администраторам
        for admin in admins:
            admin_id = admin['telegram_id']
            if admin_id:
                await context.bot.send_message(chat_id=admin_id, text=message)

        logging.info("Сообщение успешно отправлено администраторам.")
    except Exception as e:
        logging.error(f"Ошибка при уведомлении администраторов: {e}")
    finally:
        conn.close()
