import bcrypt
import logging
import pymysql.cursors
from config import DATABASE_CONFIG

# Настройка логирования
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
            cursorclass=pymysql.cursors.DictCursor  # Результаты в виде словаря
        )
        logging.debug("Успешное подключение к базе данных через PyMySQL")
        return conn
    except pymysql.MySQLError as e:
        logging.error("Ошибка подключения к базе данных: %s", e)
        raise

def hash_password(password):
    """
    Генерирует bcrypt-хэш из пароля.
    """
    try:
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        logging.debug("Хэш пароля успешно создан: %s", hashed)
        return hashed
    except Exception as e:
        logging.error("Ошибка хэширования пароля: %s", e)
        raise

def verify_password(password, hashed_password):
    """
    Проверяет пароль с использованием bcrypt.
    """
    try:
        result = bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        logging.debug("Результат проверки пароля: %s", result)
        return result
    except ValueError as ve:
        logging.error("Ошибка проверки пароля: некорректный формат хэша. %s", ve)
        raise
    except Exception as e:
        logging.error("Общая ошибка проверки пароля: %s", e)
        raise
