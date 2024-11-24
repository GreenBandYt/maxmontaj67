import bcrypt

# Хэш из базы данных
db_hash = "$2b$12$5yoQzTLonhHL3C2wDZ26mOvMcSM43y8fCtgbjRhzrYCUvjQNCqJc2"  # Замените на ваш хэш
plain_password = "byv5054byv"  # Пароль, который вы проверяете

print("[DEBUG] Проверка хэша:")
try:
    result = bcrypt.checkpw(plain_password.encode('utf-8'), db_hash.encode('utf-8'))
    print(f"[DEBUG] Пароль совпадает: {result}")
except Exception as e:
    print(f"[ERROR] Ошибка при проверке хэша: {e}")
