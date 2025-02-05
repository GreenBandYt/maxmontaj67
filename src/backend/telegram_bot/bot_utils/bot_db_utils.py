import pymysql.cursors
import logging
import os
import sys
print("Текущие пути sys.path из bot_db_utils:")
for path in sys.path:
    print(path)


# Добавляем корневой путь src в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .bot_config import BOT_DB_CONFIG  # Импортируется из backend/config.py

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def db_connect():
    """
    Устанавливает соединение с базой данных с использованием PyMySQL,
    сразу устанавливая московский часовой пояс для сессии.
    """
    try:
        logging.debug("Попытка подключения к базе данных с параметрами: %s", BOT_DB_CONFIG)
        conn = pymysql.connect(
            host=BOT_DB_CONFIG['host'],
            user=BOT_DB_CONFIG['user'],
            password=BOT_DB_CONFIG['password'],
            database=BOT_DB_CONFIG['database'],
            charset=BOT_DB_CONFIG['charset'],
            cursorclass=pymysql.cursors.DictCursor,
            init_command="SET time_zone = '+03:00'"
        )
        logging.debug("Успешное подключение к базе данных через PyMySQL")
        return conn
    except pymysql.MySQLError as e:
        logging.error("Ошибка подключения к базе данных: %s", e)
        raise
