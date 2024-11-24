from cryptography.fernet import Fernet
import bcrypt

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
    except Exception as e:
        print(f"[ERROR] Ошибка при загрузке ключа: {e}")
        raise

# Функции для шифрования и дешифрования данных
def encrypt_data(data):
    """
    Шифрует данные с использованием ключа.
    """
    try:
        key = load_key()
        fernet = Fernet(key)
        return fernet.encrypt(data.encode()).decode()
    except Exception as e:
        print(f"[ERROR] Ошибка шифрования данных: {e}")
        raise Exception("Ошибка при шифровании данных. Проверьте ключ и исходные данные.")

def decrypt_data(encrypted_data):
    """
    Дешифрует данные с использованием ключа.
    """
    try:
        key = load_key()
        fernet = Fernet(key)
        return fernet.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        print(f"[ERROR] Ошибка дешифрования данных: {e}")
        raise Exception("Ошибка при дешифровании данных. Проверьте зашифрованные данные и ключ.")

# Функции для работы с паролями
def hash_password(password):
    """
    Генерирует bcrypt-хэш из пароля.
    """
    try:
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        print(f"[DEBUG] Пароль успешно хэширован: {hashed}")
        return hashed
    except Exception as e:
        print(f"[ERROR] Ошибка при хэшировании пароля: {e}")
        raise Exception("Ошибка при хэшировании пароля. Проверьте входные данные.")

def verify_password(password, hashed_password):
    """
    Проверяет пароль с использованием bcrypt.
    """
    try:
        result = bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        print(f"[DEBUG] Результат проверки пароля: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] Ошибка при проверке пароля: {e}")
        raise Exception("Ошибка при проверке пароля. Проверьте входные данные.")
