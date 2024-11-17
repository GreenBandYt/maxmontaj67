from flask import Flask, request, jsonify, session
from utils import db_connect, verify_password, hash_password

app = Flask(__name__)

@app.route('/api/login', methods=['POST'])
def api_login():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return jsonify({'error': 'Email и пароль обязательны'}), 400

    with db_connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, password_hash, role, name FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

    if user and verify_password(password, user[1]):
        session['user_id'] = user[0]
        session['role'] = user[2]
        session['name'] = user[3]
        return jsonify({'message': 'Успешный вход', 'role': user[2], 'name': user[3]}), 200
    return jsonify({'error': 'Неверный логин или пароль'}), 401

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
