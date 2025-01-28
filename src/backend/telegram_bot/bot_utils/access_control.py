from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
import sys
import inspect


def check_access(required_role=None, required_state=None):
    """
    Декоратор для проверки роли и состояния пользователя перед выполнением функции.

    :param required_role: Роль, необходимая для доступа к функции.
    :param required_state: Состояние, необходимое для выполнения функции.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_role = context.user_data.get("role")
            user_state = context.user_data.get("state")

            # Проверяем роль
            if required_role and user_role != required_role:
                await update.message.reply_text(
                    f"⛔ У вас нет доступа к этой функции.\n"
                    f"Ваша роль: {user_role}\n"
                    f"Требуемая роль: {required_role}."
                )
                return

            # Проверяем состояние
            if required_state and user_state != required_state:
                await update.message.reply_text(
                    f"⚠️ Вы не можете выполнить это действие в текущем состоянии.\n"
                    f"Ваше состояние: {user_state}\n"
                    f"Требуемое состояние: {required_state}."
                )
                return

            # Если проверки пройдены, вызываем оригинальную функцию
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator


def find_decorated_functions():
    """
    Поиск всех функций, имеющих декораторы.
    """
    decorated_functions = []

    print("🔎 Поиск задекорированных функций...")

    for module_name, module in sys.modules.items():
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if hasattr(func, '__wrapped__'):
                print(f"✅ Найдена задекорированная функция: {func.__name__} в модуле {module_name}")
                decorated_functions.append({
                    "function_name": func.__name__,
                    "decorator": func.__wrapped__.__name__,
                    "module": module_name,
                    "description": func.__doc__ or "Описание отсутствует"
                })

    print(f"📌 Всего найдено задекорированных функций: {len(decorated_functions)}")
    return decorated_functions
