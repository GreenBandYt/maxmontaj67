import pymysql
import logging
from telegram_bot.bot_utils.bot_db_utils import db_connect


async def get_user_role(user_id: int) -> str:
    """
    Получает роль пользователя из БД.
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            query = """
                SELECT r.name AS role
                FROM users u
                JOIN roles r ON u.role = r.id
                WHERE u.telegram_id = %s
            """
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            return result['role'] if result else "new_guest"
    except Exception as e:
        raise RuntimeError(f"Ошибка получения роли пользователя: {e}")


async def get_user_state(user_id: int) -> str:
    """
    Получает текущее состояние пользователя из БД.
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            query = "SELECT user_state FROM users WHERE telegram_id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            return result['user_state'] if result else None
    except Exception as e:
        raise RuntimeError(f"Ошибка получения состояния пользователя: {e}")


async def update_user_state(user_id: int, new_state: str) -> None:

    """
    Обновляет состояние пользователя в БД.
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            query = "UPDATE users SET user_state = %s WHERE telegram_id = %s"
            cursor.execute(query, (new_state, user_id))
            logging.info(f"Состояние пользователя {user_id} будет изменено на {new_state}")

            conn.commit()
    except Exception as e:
        raise RuntimeError(f"Ошибка обновления состояния пользователя: {e}")

async def get_user_name(user_id: int) -> str:
    """
    Получает имя пользователя из базы данных по его Telegram ID.
    Возвращает имя, если оно есть, иначе None.
    """
    try:
        conn = db_connect()
        with conn.cursor() as cursor:
            query = "SELECT name FROM users WHERE telegram_id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            return result["name"] if result else None
    except Exception as e:
        logging.error(f"Ошибка при получении имени пользователя {user_id}: {e}")
        return None
    finally:
        conn.close()


async def update_user_name(user_id: int, new_name: str) -> bool:
    """
    Обновляет имя пользователя в базе данных.
    Возвращает True, если обновление прошло успешно, иначе False.
    """
    try:
        conn = db_connect()
        with conn.cursor() as cursor:
            query = "UPDATE users SET name = %s WHERE telegram_id = %s"
            cursor.execute(query, (new_name, user_id))
            conn.commit()
        logging.info(f"[DB] Имя пользователя {user_id} обновлено на '{new_name}'")
        return True
    except Exception as e:
        logging.error(f"Ошибка при обновлении имени пользователя {user_id}: {e}")
        return False
    finally:
        conn.close()
