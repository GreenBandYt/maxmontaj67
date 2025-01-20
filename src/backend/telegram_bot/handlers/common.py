from telegram import Update
from telegram.ext import ContextTypes
from bot_utils.bot_db_utils import db_connect  # Подключение к базе данных
from .keyboards.common_keyboards import guest_keyboard


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

# Обработчик текстового сообщения для проверки имени пользователя
async def process_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик текстового сообщения. Проверяет введённое имя пользователя.
    """
    user_name = update.message.text  # Получаем введённое имя пользователя
    user_id = update.effective_user.id  # Получаем telegram_id пользователя

    # Проверяем имя в базе данных
    user_data = await check_user_name_in_db(user_name)

    if user_data:
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
    else:
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
            return {
                "id": result['id'],
                "role": result['role_name']
            } if result else None
    except Exception as e:
        # Логируем ошибку подключения
        print(f"Ошибка при проверке имени в базе данных: {e}")
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
    if context.user_data.get('registration_step') != "email_request":
        # Если шаг регистрации не "email_request", пропускаем обработчик
        return

    email = update.message.text.strip()  # Получаем текст сообщения
    user = find_user_by_email(email)  # Проверяем email в базе данных

    if user:
        # Привязываем telegram_id к пользователю
        update_user_telegram_id(user['id'], update.effective_user.id)
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
        # Email не найден
        await update.message.reply_text(
            "Email не найден. Пожалуйста, проверьте данные или свяжитесь с администратором."
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
            return cursor.fetchone()  # Возвращаем первую найденную запись
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
