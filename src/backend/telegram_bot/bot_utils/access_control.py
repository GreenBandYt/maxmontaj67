from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from telegram_bot.bot_utils.bot_db_utils import db_connect
import logging
import sys
import inspect
import ast
from telegram_bot.dictionaries.states import INITIAL_STATES


def check_access(required_role=None, required_state=None):
    """
    Декоратор для проверки роли и состояния пользователя перед выполнением функции.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            # Синхронизация роли и состояния с базой данных
            is_synced = await sync_user_role_and_state(update, context)
            if not is_synced:
                return

            user_role = context.user_data.get("role", "guest")
            user_state = context.user_data.get("state", "guest_idle")

            # Логирование текущего состояния и роли перед проверкой
            logging.info(
                f"[CHECK ACCESS] Функция: {func.__name__} | Роль пользователя: {user_role}, "
                f"Состояние пользователя: {user_state} | Требуемая роль: {required_role}, "
                f"Требуемое состояние: {required_state}"
            )

            # Проверяем роль
            if required_role and required_role != "all" and user_role != required_role:
                logging.warning(
                    f"[ACCESS DENIED] Пользователь с ролью '{user_role}' попытался выполнить "
                    f"функцию '{func.__name__}', требующую роль '{required_role}'."
                )
                await update.message.reply_text(
                    f"⛔ У вас нет доступа к этой функции.\n"
                    f"Ваша роль: {user_role}\n"
                    f"Требуемая роль: {required_role}."
                )
                return

            # Проверяем состояние
            if required_state and user_state != required_state:
                logging.warning(
                    f"[ACCESS DENIED] Пользователь с состоянием '{user_state}' попытался выполнить "
                    f"функцию '{func.__name__}', требующую состояние '{required_state}'."
                )
                await update.message.reply_text(
                    f"⚠️ Вы не можете выполнить это действие в текущем состоянии.\n"
                    f"Ваше состояние: {user_state}\n"
                    f"Требуемое состояние: {required_state}."
                )
                return

            # Если проверки пройдены, вызываем оригинальную функцию
            logging.info(
                f"[ACCESS GRANTED] Пользователь с ролью '{user_role}' и состоянием '{user_state}' "
                f"получил доступ к функции '{func.__name__}'."
            )
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator


async def sync_user_role_and_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Синхронизирует роль и состояние пользователя с базой данных.
    Извлекает из БД как роль, так и состояние пользователя и обновляет context.user_data.
    Если в БД поле state пустое или None, подставляется начальное состояние из INITIAL_STATES.
    """
    user_id = update.message.from_user.id

    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            query = """
                SELECT r.name AS role, u.state AS state
                FROM users u
                JOIN roles r ON u.role = r.id
                WHERE u.telegram_id = %s
            """
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            if not result:
                await update.message.reply_text("⛔ Пользователь не найден в системе.")
                return False
            # Преобразуем результат в словарь, если это необходимо
            try:
                db_role = result["role"]
                db_state = result["state"]
            except (TypeError, KeyError):
                db_role = result[0]
                db_state = result[1]
            # Если состояние в БД пустое, подставляем начальное состояние для данной роли
            if not db_state:
                db_state = INITIAL_STATES.get(db_role, "guest_idle")
    except Exception as e:
        logging.error(f"Ошибка при извлечении роли и состояния из БД: {e}")
        await update.message.reply_text("❌ Произошла ошибка при синхронизации данных.")
        return False
    finally:
        # Не вызываем conn.close(), так как 'with' уже закрывает соединение.
        pass

    if not context.user_data:
        context.user_data.clear()

    current_role = context.user_data.get("role", "guest")
    current_state = context.user_data.get("state", "")
    if current_role != db_role or current_state != db_state:
        context.user_data["role"] = db_role
        context.user_data["state"] = db_state
        await update.message.reply_text(
            f"Ваша роль была обновлена: {db_role}. Текущее состояние: {db_state}."
        )
    return True


def find_decorated_functions():
    """
    Поиск всех функций с декоратором @check_access в модулях внутри telegram_bot.
    """
    decorated_functions = []

    print("🔎 Поиск задекорированных функций...")

    # Перебираем все загруженные модули
    for module_name, module in list(sys.modules.items()):
        if module and module_name.startswith("telegram_bot"):
            for name, func in inspect.getmembers(module, inspect.isfunction):
                # Проверяем, есть ли у функции декоратор
                if hasattr(func, "__wrapped__"):
                    decorator = func.__wrapped__

                    # Инициализируем переменные
                    required_role = "Не указано"
                    required_state = "Не указано"

                    # Попытка извлечь параметры через __closure__
                    if hasattr(decorator, "__closure__") and decorator.__closure__:
                        closure_vars = [var.cell_contents for var in decorator.__closure__ if var.cell_contents]

                        for var in closure_vars:
                            if isinstance(var, str):
                                if var in INITIAL_STATES.keys():  # Проверяем по известным ролям
                                    required_role = var
                                elif "idle" in var or "active" in var or "busy" in var:
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
                                            required_role = keyword.value.s
                                        if keyword.arg == "required_state":
                                            required_state = keyword.value.s
                        except Exception as e:
                            logging.error(f"⚠ Ошибка при разборе кода {func.__name__}: {e}")

                    # Логируем найденную функцию
                    print(f"✅ Найдена задекорированная функция: {name} (Роль: {required_role}, Состояние: {required_state})")

                    decorated_functions.append({
                        "function_name": name,
                        "decorator": decorator.__name__,
                        "module": module_name,
                        "description": func.__doc__ or "Описание отсутствует",
                        "required_role": required_role,
                        "required_state": required_state
                    })

    print(f"📌 Всего найдено задекорированных функций: {len(decorated_functions)}")
    return decorated_functions
