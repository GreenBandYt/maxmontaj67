# src/backend/telegram_bot/bot_utils/messages/admin_user_messages.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import logging


def handle_user_message_to_admin(user, message_text):
    """
    Форматирует сообщение от пользователя для отправки администраторам с инлайн-кнопкой "Ответить".

    :param user: dict - данные пользователя (имя, username, telegram_id).
    :param message_text: str - текст сообщения.
    :return: tuple - отформатированное сообщение и кнопка.
    """
    user_info = f"{user.get('first_name', 'Пользователь')} (@{user.get('username', 'Не указан')})"
    formatted_message = f"""
📩 *Сообщение от {user_info}:*
📝 {message_text}
"""

    # Используем telegram_id пользователя для callback_data
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 Ответить пользователю", callback_data=f"reply_to_{user['telegram_id']}")]
    ])

    return formatted_message, reply_markup


async def handle_reply_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик кнопки "📩 Ответить пользователю".
    """
    query = update.callback_query
    callback_data = query.data  # Пример callback_data: "reply_to_123456789"

    # Извлекаем Telegram ID пользователя
    user_id = callback_data.split("_")[-1]

    # Сохраняем Telegram ID пользователя в context.user_data
    context.user_data["reply_to_user"] = user_id

    # Уведомляем администратора
    await query.answer("Введите текст ответа пользователю.")
    await query.message.reply_text("Введите текст ответа пользователю:")

    # Подтверждаем callback
    await query.answer()


async def handle_reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для отправки ответа пользователю.
    """
    admin_id = update.message.from_user.id
    user_id = context.user_data.get("reply_to_user")  # Получаем сохранённый Telegram ID пользователя
    reply_text = update.message.text

    if not user_id:
        await update.message.reply_text("❌ Ошибка: Нет пользователя для ответа.")
        return

    try:
        # Отправляем сообщение пользователю
        await context.bot.send_message(chat_id=user_id, text=f"Администратор:\n{reply_text}")
        await update.message.reply_text("✅ Сообщение отправлено пользователю.")
    except Exception as e:
        logging.error(f"[REPLY MESSAGE] Ошибка при отправке сообщения пользователю {user_id}: {e}")
        await update.message.reply_text("❌ Не удалось отправить сообщение пользователю.")

    # Сбрасываем состояние
    context.user_data["reply_to_user"] = None
