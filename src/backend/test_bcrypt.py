import bcrypt

plain_password = "byv5054byv"
hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

print(f"Plain: {plain_password}")
print(f"Hashed: {hashed_password}")
print(f"Verified: {bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))}")  # Ожидается: True
