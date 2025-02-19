# src/backend/telegram_bot/handlers/guest/guest_menu.py

from telegram import Update
from telegram.ext import ContextTypes, CallbackContext
from .guest_keyboards import guest_keyboard, generate_email_error_keyboard, generate_role_selection_keyboard
from telegram_bot.bot_utils.access_control import check_access, check_state
from telegram_bot.bot_utils.db_utils import update_user_state, get_user_name, update_user_name
from telegram_bot.bot_utils.bot_db_utils import db_connect
from telegram import InlineKeyboardMarkup, InlineKeyboardButton


import logging

@check_access(required_role="new_guest", required_state="guest_idle")
async def start_guest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Стартовая страница для гостя.
    """
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    # ✅ Логирование входа в гостевую зону
    logging.info(f"[GUEST] Пользователь {user_id} ({user_name}) зашел в гостевую зону.")

    await update.message.reply_text(
        f"Добро пожаловать, {user_name}!\n"
        "Вы находитесь в гостевой зоне. Зарегистрируйтесь, чтобы получить доступ к функционалу.",
        reply_markup=guest_keyboard()  # Клавиатура для гостя
    )



@check_access(required_role="new_guest", required_state="guest_idle")
async def handle_guest_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка кнопки "✍️ Регистрация".
    Запрашивает у пользователя подтверждение имени из Telegram или ввод нового имени.
    """
    user_id = update.effective_user.id
    telegram_name = update.effective_user.first_name

    # ✅ Логирование старта регистрации
    logging.info(f"[GUEST] Пользователь {user_id} начал регистрацию.")

    # ✅ Проверяем, есть ли имя в БД
    user_name = await get_user_name(user_id)

    if user_name:
        logging.info(f"[GUEST] Пользователь {user_id} уже имеет имя '{user_name}'. Предлагаем его оставить.")
    else:
        user_name = telegram_name
        logging.info(f"[GUEST] Имя в БД отсутствует. Предлагаем Telegram-имя: '{user_name}'.")

    # ✅ Меняем состояние пользователя в БД на "registration_name"
    await update_user_state(user_id, "registration_name")

    # ✅ Сохраняем предложенное имя в context
    context.user_data["suggested_name"] = user_name

    # ✅ Отправляем сообщение с кнопками
    await update.message.reply_text(
        f"Мы получили ваше имя из Telegram: *{user_name}*.\n"
        "Хотите использовать его?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Да, использовать", callback_data="use_name")],
            [InlineKeyboardButton("❌ Нет, ввести другое", callback_data="enter_name")]
        ])
    )

@check_state(required_state="registration_name")
async def handle_use_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает нажатие кнопки "✅ Да, использовать".
    Сохраняет предложенное имя в БД и переходит к выбору роли.
    """
    query = update.callback_query
    user_id = query.from_user.id

    # ✅ Получаем предложенное имя из context
    suggested_name = context.user_data.get("suggested_name")

    if not suggested_name:
        logging.error(f"[GUEST] Ошибка: предложенное имя отсутствует для пользователя {user_id}.")
        await query.edit_message_text("Ошибка: предложенное имя не найдено. Попробуйте ввести имя заново.")
        return

    logging.info(f"[GUEST] Пользователь {user_id} нажал '✅ Да, использовать'. Сохраняем имя: {suggested_name}")

    # ✅ Обновляем имя пользователя в БД
    await update_user_name(user_id, suggested_name)

    # ✅ Меняем состояние пользователя в БД на "registration_role"
    await update_user_state(user_id, "registration_role")

    # ✅ Отправляем пользователю подтверждение
    await query.edit_message_text(
        f"Ваше имя сохранено: *{suggested_name}* ✅\n\nТеперь выберите вашу роль:",
        parse_mode="Markdown",
        reply_markup=generate_role_selection_keyboard()
    )






@check_state(required_state="registration_name")
async def process_registration_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает ввод имени пользователем.
    """
    user_id = update.effective_user.id
    user_name = update.message.text.strip()  # Получаем имя

    logging.info(f"[GUEST] Пользователь {user_id} ввел имя '{user_name}'. Проверяем уникальность...")

    # Проверяем, занято ли имя
    if await is_name_taken(user_name):
        logging.info(f"❌ Имя '{user_name}' уже используется. Запрашиваем другое.")
        await update.message.reply_text(
            "Это имя уже занято. Пожалуйста, попробуйте другое."
        )
        return

    # ✅ Имя свободно - сохраняем
    logging.info(f"✅ Имя '{user_name}' свободно. Переход к выбору роли.")

    # Сохраняем имя в context.user_data
    context.user_data["registration_name"] = user_name

    # Меняем состояние пользователя в БД на "registration_role"
    await update_user_state(user_id, "registration_role")

    # Отправляем inline-кнопки для выбора роли
    await update.message.reply_text(
        "Выберите вашу желаемую роль:",
        reply_markup=generate_role_selection_keyboard()
    )


@check_access(required_role="new_guest", required_state="registration_role")
async def handle_guest_role_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает этап выбора роли пользователем во время регистрации.
    """
    query = update.callback_query
    user_id = update.effective_user.id

    logging.info(f"[GUEST] Пользователь {user_id} выбирает роль для регистрации.")

    await query.message.reply_text(
        "Выберите вашу роль в системе:",
        reply_markup=generate_role_selection_keyboard()
    )

    # Сохраняем состояние в context
    context.user_data["registration_step"] = "registration_role"

@check_access(required_role="new_guest", required_state="registration_role")
async def handle_guest_choose_executor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает выбор роли "Исполнитель".
    """
    query = update.callback_query
    user_id = update.effective_user.id

    logging.info(f"[GUEST] Пользователь {user_id} выбрал роль 'Исполнитель'.")

    # Обновляем состояние в контексте
    context.user_data["registration_role"] = "executor"
    context.user_data["registration_step"] = "registration_finish"

    await query.edit_message_text(
        "Вы выбрали роль *Исполнитель*.\n"
        "Ваши данные отправлены администратору на подтверждение.",
        parse_mode="Markdown"
    )

    # Обновляем состояние пользователя в БД
    await update_user_state(user_id, "registration_finish")

    # Отправляем уведомление администратору
    await notify_admin_about_registration(update, context)


@check_access(required_role="new_guest", required_state="registration_role")
async def handle_guest_choose_specialist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает выбор роли "Специалист".
    """
    query = update.callback_query
    await query.answer("Роль 'Специалист' временно недоступна.", show_alert=True)


@check_access(required_role="new_guest", required_state="registration_role")
async def handle_guest_choose_customer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает выбор роли "Заказчик".
    """
    query = update.callback_query
    await query.answer("Роль 'Заказчик' временно недоступна.", show_alert=True)


@check_access(required_role="new_guest", required_state="registration_role")
async def handle_guest_role_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает нажатие кнопки "Назад" при выборе роли.
    """
    query = update.callback_query
    user_id = update.effective_user.id

    logging.info(f"[GUEST] Пользователь {user_id} отменил выбор роли и вернулся назад.")

    # Сбрасываем состояние выбора роли
    context.user_data.pop("registration_role", None)
    context.user_data["registration_step"] = "registration_name"

    await query.edit_message_text(
        "Вы вернулись назад.\n"
        "Введите ваше имя для регистрации."
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
