import pymysql.cursors
import bcrypt
import logging
from config import DATABASE_CONFIG

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def db_connect():
    """
    Устанавливает соединение с базой данных с использованием PyMySQL.
    """
    try:
        logging.debug("Попытка подключения к базе данных с параметрами: %s", DATABASE_CONFIG)
        conn = pymysql.connect(
            host=DATABASE_CONFIG['host'],
            user=DATABASE_CONFIG['user'],
            password=DATABASE_CONFIG['password'],
            database=DATABASE_CONFIG['database'],
            charset=DATABASE_CONFIG['charset'],
            cursorclass=pymysql.cursors.DictCursor  # Используем DictCursor для работы с результатами как со словарями
        )
        logging.debug("[DEBUG] Успешное подключение к базе данных через PyMySQL.")
        return conn
    except pymysql.MySQLError as e:
        logging.error(f"[ERROR] Ошибка подключения к базе данных: {e}")
        raise

def hash_password(password):
    """
    Генерирует bcrypt-хэш из пароля.
    """
    try:
        logging.debug("[DEBUG] Попытка хэширования пароля.")
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        logging.debug("[DEBUG] Пароль: %s, Хэш: %s", password, hashed)
        return hashed
    except Exception as e:
        logging.error(f"[ERROR] Ошибка хэширования пароля: {e}")
        raise

def verify_password(password, hashed_password):
    """
    Проверяет пароль с использованием bcrypt.
    """
    try:
        logging.debug("[DEBUG] Попытка проверки пароля.")
        result = bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        logging.debug(f"[DEBUG] Результат проверки пароля: {result}")
        return result
    except Exception as e:
        logging.error(f"[ERROR] Ошибка проверки пароля: {e}")
        raise
