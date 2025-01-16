from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Импорт токена из защищённой папки
try:
    from protected.FG_Telegram_Token import TELEGRAM_BOT_TOKEN
except ImportError:
    raise ImportError("Токен не найден! Убедитесь, что он находится в файле protected/FG_Telegram_Token.py")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start.
    """
    await update.message.reply_text(
        "Добро пожаловать в CRM-бот maxmontaj67! 🎉\n"
        "Используйте /help для получения списка доступных команд."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /help.
    """
    await update.message.reply_text(
        "Список доступных команд:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать список команд"
    )

def run_bot():
    """
    Запуск Telegram-бота.
    """
    # Проверка наличия токена
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("Токен Telegram не указан!")

    # Создание приложения Telegram
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    print("Telegram-бот запущен. Ожидание сообщений...")
    application.run_polling()

if __name__ == "__main__":
    run_bot()
