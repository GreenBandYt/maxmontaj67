from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
import sys
import inspect
import ast



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


import inspect
import sys
from functools import wraps

def find_decorated_functions():
    """
    Поиск всех функций с декоратором @check_access и извлечение их параметров.
    """
    decorated_functions = []

    print("🔎 Поиск задекорированных функций...")

    for module_name, module in list(sys.modules.items()):
        if module and module_name.startswith("telegram_bot.handlers"):
            for name, func in inspect.getmembers(module, inspect.isfunction):
                if hasattr(func, "__wrapped__"):
                    decorator = func.__wrapped__

                    # Инициализируем переменные
                    required_role = "Не указано"
                    required_state = "Не указано"

                    # Попытка извлечь аргументы через __closure__
                    if hasattr(decorator, "__closure__") and decorator.__closure__:
                        closure_vars = [var.cell_contents for var in decorator.__closure__ if var.cell_contents]

                        for var in closure_vars:
                            if isinstance(var, str):
                                if "guest" in var or "admin" in var or "executor" in var:
                                    required_role = var
                                if "idle" in var or "active" in var or "busy" in var:
                                    required_state = var

                    # Если не нашли в __closure__, пытаемся извлечь параметры из исходного кода
                    if required_role == "Не указано" or required_state == "Не указано":
                        try:
                            source_code = inspect.getsource(func)
                            tree = ast.parse(source_code)
                            for node in ast.walk(tree):
                                if isinstance(node, ast.Call) and hasattr(node.func, 'id') and node.func.id == "check_access":
                                    for keyword in node.keywords:
                                        if keyword.arg == "required_role":
                                            required_role = keyword.value.s  # Значение строкового аргумента
                                        if keyword.arg == "required_state":
                                            required_state = keyword.value.s
                        except Exception as e:
                            print(f"⚠ Ошибка при разборе кода {func.__name__}: {e}")

                    print(f"✅ Найдена задекорированная функция: {func.__name__} (Роль: {required_role}, Состояние: {required_state})")

                    decorated_functions.append({
                        "function_name": func.__name__,
                        "decorator": decorator.__name__,
                        "module": module_name,
                        "description": func.__doc__ or "Описание отсутствует",
                        "required_role": required_role,
                        "required_state": required_state
                    })

    print(f"📌 Всего найдено задекорированных функций: {len(decorated_functions)}")
    return decorated_functions
