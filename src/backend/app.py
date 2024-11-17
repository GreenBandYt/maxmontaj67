from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
from config import SESSION_CONFIG
from utils import db_connect, verify_password

app = Flask(__name__)

# Настройка сессий из config.py
app.config['SESSION_TYPE'] = SESSION_CONFIG['type']
app.config['SESSION_PERMANENT'] = SESSION_CONFIG['permanent']
app.config['SESSION_FILE_DIR'] = SESSION_CONFIG['file_dir']
Session(app)

# Главная страница
@app.route('/')
def home():
    user_name = session.get('name', 'Гость')
    role = session.get('role', None)

    # Логика маршрутов в зависимости от роли пользователя
    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'dispatcher':
        return redirect(url_for('dispatcher_dashboard'))
    elif role == 'specialist':
        return redirect(url_for('specialist_dashboard'))
    elif role == 'executor':
        return redirect(url_for('executor_dashboard'))
    elif role == 'customer':
        return redirect(url_for('customer_dashboard'))
    else:
        return render_template('index.html', user_name=user_name)

# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, password_hash, role, name FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

        if user and verify_password(password, user[1]):
            session['user_id'] = user[0]
            session['role'] = user[2]
            session['name'] = user[3]
            return redirect(url_for('home'))
        else:
            return "Неверный логин или пароль", 401

    return render_template('login.html')

# Выход из системы
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Страницы для каждой роли
@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html', user_name=session.get('name', 'Гость'))

@app.route('/dispatcher_dashboard')
def dispatcher_dashboard():
    return render_template('dispatcher_dashboard.html', user_name=session.get('name', 'Гость'))

@app.route('/specialist_dashboard')
def specialist_dashboard():
    return render_template('specialist_dashboard.html', user_name=session.get('name', 'Гость'))

@app.route('/executor_dashboard')
def executor_dashboard():
    return render_template('executor_dashboard.html', user_name=session.get('name', 'Гость'))

@app.route('/customer_dashboard')
def customer_dashboard():
    return render_template('customer_dashboard.html', user_name=session.get('name', 'Гость'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
