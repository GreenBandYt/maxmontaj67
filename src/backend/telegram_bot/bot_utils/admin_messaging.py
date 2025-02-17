# src/backend/telegram_bot/bot_utils/admin_messaging.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import logging
import asyncio
import pymysql
from telegram_bot.bot_utils.bot_db_utils import db_connect
from telegram_bot.bot_utils.access_control import check_access, check_state
from telegram_bot.bot_utils.db_utils import update_user_state, get_user_role
from telegram_bot.dictionaries.states import INITIAL_STATES


@check_state(required_state="specialist_idle")  # Для примера, тут может быть любое состояние из INITIAL_STATES
async def handle_message_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("🛠️ Вызван Обработчик кнопки 📞 Написать администратору")
    """
    Обработчик кнопки "📞 Написать администратору".
    """
    user_id = update.effective_user.id

    # Устанавливаем новое состояние
    await update_user_state(user_id, "writing_message")

    await update.message.reply_text("Напишите текст вашего сообщения для администратора. 📩")

@check_state("writing_message")  # Проверяем, что пользователь находится в состоянии "writing_message"
async def process_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("🛠️ Вызван process_admin_message")
    """
    Обрабатывает текст сообщения, введённый пользователем для администратора.
    """
    # Получаем текст сообщения
    admin_message = update.message.text.strip()

    if not admin_message:
        # Если текст пустой, уведомляем пользователя
        await update.message.reply_text("❌ Сообщение не может быть пустым. Пожалуйста, напишите текст сообщения.")
        return

    # Формируем текст сообщения
    user = update.effective_user
    formatted_message = f"📩 Сообщение от {user.full_name} (@{user.username}):\n\n{admin_message}"

    # Создаём инлайн-кнопку
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("📩 Ответить пользователю", callback_data=f"reply_to_{user.id}")
    ]])

    # Отправляем сообщение администраторам
    success = await send_message_to_admins(context, formatted_message, reply_markup)

    if success:
        await update.message.reply_text("✅ Ваше сообщение успешно отправлено администраторам. Ожидайте ответа.")
    else:
        await update.message.reply_text("❌ Администраторы не найдены или произошла ошибка.")

    # Получаем роль пользователя из БД
    role = context.user_data.get("role")  # Если роль кэшируется в context.user_data
    if not role:
        # В случае, если роли нет в кэше, получаем её из базы данных
        role = await get_user_role(user.id)

    # Устанавливаем начальное состояние для этой роли
    initial_state = INITIAL_STATES.get(role, "guest_idle")  # На случай отсутствия роли по умолчанию

    # Сбрасываем состояние пользователя в БД
    await update_user_state(user.id, initial_state)



async def send_message_to_admins(context: ContextTypes.DEFAULT_TYPE, message: str, reply_markup=None):
    logging.info("🛠️ Вызван send_message_to_admins")

    """
    Отправляет сообщение всем администраторам.
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            query = """
                SELECT telegram_id
                FROM users
                WHERE role = (SELECT id FROM roles WHERE name = 'admin')
                  AND telegram_id IS NOT NULL
            """
            cursor.execute(query)
            admins = cursor.fetchall()

        if not admins:
            logging.warning("❗ Администраторы не найдены.")
            return False

        for admin in admins:
            admin_id = admin.get("telegram_id")
            try:
                await context.bot.send_message(chat_id=admin_id, text=message, reply_markup=reply_markup)
            except Exception as e:
                logging.error(f"Ошибка отправки сообщения админу {admin_id}: {e}")
        return True
    except Exception as e:
        logging.error(f"Ошибка отправки сообщений администраторам: {e}")
        return False

@check_state(required_state="admin_idle")
async def handle_reply_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("🛠️ Вызван handle_reply_button")
    """
    Обработчик кнопки "📩 Ответить пользователю".
    Переводит администратора в состояние "replying_to_user".
    """
    query = update.callback_query
    callback_data = query.data  # Пример callback_data: "reply_to_5254094063"

    # Извлекаем telegram_id пользователя из callback_data
    user_id = callback_data.split("_")[-1]
    logging.info(f"Сохраняем ID пользователя {user_id} для ответа в context.user_data['reply_to_user']")

    # Сохраняем ID пользователя, которому нужно ответить
    context.user_data["reply_to_user"] = user_id

    # Меняем состояние администратора
    admin_id = update.effective_user.id
    await update_user_state(admin_id, "replying_to_user")

    # Добавляем небольшую задержку
    await asyncio.sleep(1)  # Полсекунды задержки


    # Уведомляем администратора о переходе в режим ответа
    await query.answer("Введите текст ответа пользователю.")
    await query.message.reply_text("Введите текст ответа пользователю:")

    logging.info(f"Администратор {admin_id} перешел в состояние 'replying_to_user' для ответа пользователю {user_id}")

@check_state(required_state="replying_to_user")
async def handle_reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("🛠️ Вызван handle_reply_message")
    logging.info(f"ID пользователя для ответа: {context.user_data.get('reply_to_user')}")

    """
    Обработчик для отправки ответа пользователю.
    """
    admin_id = update.effective_user.id
    user_id = context.user_data.get("reply_to_user")  # Получаем ID пользователя, которому отправляем ответ
    reply_text = update.message.text

    if not user_id:
        await update.message.reply_text("❌ Ошибка: Нет пользователя для ответа.")
        return

    if not reply_text.strip():
        await update.message.reply_text("❌ Ответ не может быть пустым.")
        return

    try:
        # Отправляем сообщение пользователю
        await context.bot.send_message(chat_id=user_id, text=f"Администратор:\n{reply_text}")
        await update.message.reply_text("✅ Сообщение успешно отправлено пользователю.")

        logging.info(f"Администратор {admin_id} отправил сообщение пользователю {user_id}: {reply_text}")

    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
        await update.message.reply_text("❌ Не удалось отправить сообщение пользователю.")

    finally:
        # Сбрасываем ID пользователя для ответа
        context.user_data["reply_to_user"] = None

        # Возвращаем состояние администратора к исходному
        await update_user_state(admin_id, "admin_idle")
        logging.info(f"Состояние администратора {admin_id} возвращено к 'admin_idle'")
