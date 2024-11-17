import mysql.connector
import bcrypt
from config import DATABASE_CONFIG

def db_connect():
    """
    Устанавливает соединение с базой данных.
    """
    try:
        conn = mysql.connector.connect(
            **DATABASE_CONFIG,
            charset='utf8mb4',
            collation='utf8mb4_general_ci'
        )
        print("[DEBUG] Успешное подключение к базе данных")
        return conn
    except mysql.connector.Error as e:
        print(f"[ERROR] Ошибка подключения к базе данных: {e}")
        raise

def hash_password(password):
    """
    Генерирует bcrypt-хэш из пароля.
    """
    try:
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        print(f"[DEBUG] Пароль: {password}, Хэш: {hashed}")
        return hashed
    except Exception as e:
        print(f"[ERROR] Ошибка хэширования пароля: {e}")
        raise

def verify_password(password, hashed_password):
    """
    Проверяет пароль с использованием bcrypt.
    """
    try:
        result = bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        print(f"[DEBUG] Пароль (plain): {password}")
        print(f"[DEBUG] Хэш из базы: {hashed_password}")
        print(f"[DEBUG] Результат проверки: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] Ошибка проверки пароля: {e}")
        raise
