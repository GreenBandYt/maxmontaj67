from werkzeug.security import check_password_hash

hashed_password = "$2b$12$nAPq5rto7qbIjhZiAO/lNeuDC9ywQREMD2TJbV3iZCayMdf/H/BMa"
plain_password = "byv5054byv"

# Тест проверки хэша
print(check_password_hash(hashed_password, plain_password))  # Ожидается: True
