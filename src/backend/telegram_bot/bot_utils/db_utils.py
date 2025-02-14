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
