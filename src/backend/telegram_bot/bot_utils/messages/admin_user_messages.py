from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot_utils.bot_db_utils import db_connect
from bot_utils.access_control import check_access
from telegram_bot.dictionaries.states import INITIAL_STATES
import logging
import traceback


# Обработчик кнопки "📞 Написать администратору"
async def handle_user_message_to_admin(update, context):
    """
    Обрабатывает нажатие кнопки "📞 Написать администратору".
    Устанавливает состояние "awaiting_admin_message" и обновляет его в БД.
    """
    user = {
        "id": update.message.from_user.id,
        "first_name": update.message.from_user.first_name,
        "username": update.message.from_user.username,
    }

    logging.info(f"📩 Пользователь {user['first_name']} (@{user['username']}) начал писать администратору.")
    await update.message.reply_text("Введите сообщение для администратора, и мы его передадим.")

    # Обновляем состояние в БД
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            # Логируем SQL-запрос и параметры перед выполнением
            logging.info(
                f"Попытка обновления состояния: query='UPDATE users SET state = %s WHERE telegram_id = %s', params=('awaiting_admin_message', {user['id']})")

            query = "UPDATE users SET state = %s WHERE telegram_id = %s"
            cursor.execute(query, ("awaiting_admin_message", user["id"]))
            conn.commit()
            logging.info("✅ Изменения сохранены в базе данных.")
    except Exception as e:
        # Логируем полный стек ошибки для диагностики
        logging.error(f"❌ Ошибка обновления состояния в БД: {e}")
        logging.error(f"Стек вызовов: {traceback.format_exc()}")
        await update.message.reply_text("Произошла ошибка при обновлении состояния. Попробуйте снова.")
        return

    # Искусственная пауза для гарантии синхронизации (если база работает медленно)
    import asyncio
    await asyncio.sleep(2)

    # Устанавливаем локальное состояние
    context.user_data["state"] = "awaiting_admin_message"
    context.user_data["user_info"] = user
    logging.info(f"🔄 Локальное состояние пользователя изменено на: 'awaiting_admin_message'")

    # Лог перед завершением функции
    logging.info("✅ Обработчик handle_user_message_to_admin завершен.")


# Обработчик ввода сообщения для администратора
# @check_access(required_role="all", required_state="awaiting_admin_message")
async def process_user_message(update, context):
    """
    Обрабатывает сообщение, которое пользователь хочет отправить администратору.
    После успешной отправки сбрасывает состояние до начального (для текущей роли)
    и обновляет это значение в базе данных.
    """
    logging.info("📥 Обработка входящего сообщения от пользователя.")

    # Получаем роль пользователя
    user_role = context.user_data.get("role", "guest")
    logging.info(f"👤 Роль пользователя: {user_role}")

    # Проверяем наличие данных о пользователе (которые были установлены в handle_user_message_to_admin)
    user = context.user_data.get("user_info")
    if not user:
        logging.error("❌ Ошибка: состояние 'user_info' отсутствует.")
        await update.message.reply_text("❌ Ошибка: нет ожидающего сообщения.")
        return

    # Формируем сообщение для администратора
    message_text = update.message.text
    logging.info(f"📨 Пользователь {user['first_name']} отправил сообщение: {message_text}")

    formatted_message, reply_markup = format_user_message_to_admin(user, message_text)

    # Извлекаем ID администраторов из базы данных
    admin_ids = []
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            query = "SELECT telegram_id FROM users WHERE role = 'admin'"
            logging.info(f"📡 Выполнение запроса: {query}")
            cursor.execute(query)
            admin_ids = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logging.error(f"❌ Ошибка при получении ID администраторов: {e}")
        await update.message.reply_text("❌ Не удалось отправить сообщение администраторам.")
        return

    if not admin_ids:
        logging.warning("❌ В системе нет администраторов.")
        await update.message.reply_text("❌ В системе нет администраторов.")
        return

    # Отправляем сообщение всем администраторам
    for admin_id in admin_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=formatted_message,
                parse_mode="Markdown",
                reply_markup=reply_markup,
            )
            logging.info(f"📤 Сообщение отправлено администратору с ID: {admin_id}")
        except Exception as e:
            logging.error(f"❌ Не удалось отправить сообщение администратору {admin_id}: {e}")

    # Подтверждаем отправку сообщения пользователю
    await update.message.reply_text("✅ Ваше сообщение отправлено администраторам.")

    # Сбрасываем состояние пользователя до начального для его роли.
    # Здесь определяем переменную initial_state, которая потом используется в запросе к БД.
    initial_state = INITIAL_STATES.get(user_role, "guest_idle")
    context.user_data["state"] = initial_state
    logging.info(f"🔄 Локальное состояние пользователя сброшено на: {initial_state}")

    # Обновляем состояние в базе данных. Используем REPLACE для удаления пробелов из telegram_id.
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            query = "UPDATE users SET state = %s WHERE REPLACE(telegram_id, ' ', '') = %s"
            cursor.execute(query, (initial_state, str(context.user_data.get("telegram_id"))))
        conn.commit()
        logging.info("✅ Состояние в БД сброшено на начальное")
    except Exception as e:
        logging.error(f"❌ Ошибка при сбросе состояния в БД: {e}")

    # Очищаем временные данные (удаляем user_info)
    context.user_data.pop("user_info", None)
    logging.info("🧹 Очищены временные данные пользователя.")



# Утилитарная функция для форматирования сообщения
def format_user_message_to_admin(user, message_text):
    """
    Форматирует сообщение пользователя для отправки администратору.
    """
    logging.info(f"📜 Форматирование сообщения пользователя ID: {user['id']}")
    formatted_message = (
        f"📩 *Новое сообщение от пользователя:*\n"
        f"👤 *Имя*: {user['first_name']} (Username: @{user['username']})\n"
        f"🆔 *ID*: {user['id']}\n\n"
        f"✉️ *Сообщение:*\n{message_text}"
    )
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Ответить", callback_data=f"reply_to_user_{user['id']}")]
    ])
    return formatted_message, reply_markup
