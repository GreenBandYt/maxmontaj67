from cryptography.fernet import Fernet
from werkzeug.security import generate_password_hash, check_password_hash

# Функция для загрузки ключа из файла
def load_key():
    """
    Загружает ключ шифрования из файла `secret.key`.
    """
    try:
        with open('/media/sf_ShareFolder/maxmontaj67/protected/secret.key', 'rb') as key_file:
            return key_file.read()
    except FileNotFoundError:
        raise Exception("Файл с ключом шифрования не найден! Убедитесь, что 'secret.key' находится в защищённой папке.")

# Функции для шифрования и дешифрования данных
def encrypt_data(data):
    """
    Шифрует данные с использованием ключа.
    """
    key = load_key()
    fernet = Fernet(key)
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    """
    Дешифрует данные с использованием ключа.
    """
    key = load_key()
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_data.encode()).decode()

# Функции для работы с паролями
def hash_password(password):
    """
    Генерирует bcrypt-хэш из пароля.
    """
    try:
        hashed = generate_password_hash(password)
        print(f"[DEBUG] Пароль успешно хэширован.")
        return hashed
    except Exception as e:
        print(f"[ERROR] Ошибка при хэшировании пароля: {e}")
        raise

def verify_password(password, password_hash):
    """
    Проверяет соответствие пароля (в открытом виде) и его хэшированного значения.
    """
    try:
        return check_password_hash(password_hash, password)
    except Exception as e:
        print(f"[ERROR] Ошибка при проверке пароля: {e}")
        return False
