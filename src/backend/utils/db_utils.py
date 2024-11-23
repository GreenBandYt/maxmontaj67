import mysql.connector
from config import DATABASE_CONFIG

def db_connect():
    """
    Устанавливает соединение с базой данных.
    """
    try:
        conn = mysql.connector.connect(**DATABASE_CONFIG)
        print("[DEBUG] Успешное подключение к базе данных")
        return conn
    except mysql.connector.Error as e:
        print(f"[ERROR] Ошибка подключения к базе данных: {e}")
        raise
