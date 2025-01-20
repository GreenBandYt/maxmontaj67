from telegram import Update
from telegram.ext import ContextTypes

from backend.telegram_bot.bot_utils.bot_db_utils import db_connect






# Обработчик команды /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start. Приветствует пользователя в зависимости от его роли.
    """
    user_id = update.effective_user.id  # Получаем ID пользователя
    user_name = update.effective_user.first_name  # Получаем имя пользователя

    # Логика определения роли пользователя (пример проверки в базе)
    role = await get_user_role(user_id)

    if role == "guest":
        # Ответ для незарегистрированного пользователя
        await update.message.reply_text(
            f"Привет, {user_name}!\n"
            "Вы не зарегистрированы в системе. Пожалуйста, пройдите регистрацию, чтобы продолжить."
        )
        # Вызываем клавиатуру для гостя (будет добавлена в common_keyboards)
        from .keyboards.common_keyboards import guest_keyboard
        await update.message.reply_text("Выберите действие:", reply_markup=guest_keyboard())
    else:
        # Ответ для зарегистрированного пользователя
        await update.message.reply_text(
            f"Добро пожаловать, {user_name}!\n"
            f"Ваша роль: {role}.\n"
            "Что вы хотите сделать?"
        )
        # Здесь можно добавить клавиатуры для зарегистрированных ролей

# Пример функции получения роли пользователя из базы
async def get_user_role(user_id: int) -> str:
    """
    Проверяет роль пользователя по его ID.
    Возвращает строку с ролью: "guest" или роль из базы данных.
    """
    # Здесь будет запрос в базу данных, пока используем заглушку
    user_data = {12345: "admin", 67890: "customer"}  # Пример данных
    return user_data.get(user_id, "guest")


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

# Обработчик кнопки "Регистрация"
#
# async def test_db_roles():
#     """
#     Выполняет тестовый запрос к базе данных.
#     Цель: проверить доступные роли в таблице roles.
#     """
#     conn = db_connect()  # Устанавливаем подключение
#     try:
#         with conn.cursor() as cursor:
#             query = "SELECT id, name FROM roles;"  # Запрос для получения данных из таблицы roles
#             cursor.execute(query)
#             roles = cursor.fetchall()
#             print("Доступные роли:", roles)  # Логируем роли для проверки
#     finally:
#         conn.close()  # Закрываем соединение