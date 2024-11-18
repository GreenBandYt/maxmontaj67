from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
from config import SESSION_CONFIG
from utils import db_connect, verify_password
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Настройка сессий из config.py
app.config['SESSION_TYPE'] = SESSION_CONFIG['type']
app.config['SESSION_PERMANENT'] = SESSION_CONFIG['permanent']
app.config['SESSION_FILE_DIR'] = SESSION_CONFIG['file_dir']
Session(app)

ROLE_ROUTES = {
    'Administrator': 'admin_dashboard',
    'Dispatcher': 'dispatcher_dashboard',
    'Specialist': 'specialist_dashboard',
    'Executor': 'executor_dashboard',
    'Customer': 'customer_dashboard'
}


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Обработка входа
        email = request.form['email']
        password = request.form['password']

        try:
            # Подключение к базе данных
            with db_connect() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT u.id, u.password_hash, r.name AS role, u.name
                    FROM users u
                    JOIN roles r ON u.role = r.id
                    WHERE u.email = %s
                """, (email,))
                user = cursor.fetchone()

            if user and verify_password(password, user['password_hash']):
                # Установка данных сессии
                session['user_id'] = user['id']
                session['role'] = user['role']
                session['name'] = user['name']
                print(f"[DEBUG] Успешный вход: role={user['role']}, name={user['name']}")

                # Перенаправление на страницу в зависимости от роли
                return redirect(url_for(ROLE_ROUTES.get(user['role'], 'home')))
            else:
                # Неверные данные
                return render_template('index.html', error="Неверный логин или пароль")

        except Exception as e:
            # Логирование ошибки
            print(f"[ERROR] Ошибка при выполнении SQL-запроса: {e}")
            return render_template('index.html', error="Ошибка на сервере. Попробуйте позже.")

    # GET-запрос: отображение главной страницы
    user_name = session.get('name', 'Гость')
    role = session.get('role', None)

    if role in ROLE_ROUTES:
        return redirect(url_for(ROLE_ROUTES[role]))

    # Если пользователь не авторизован, отображаем главную страницу для гостей
    return render_template('index.html', user_name=user_name)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        role = request.form['role']

        # Проверка совпадения паролей
        if password != password_confirm:
            return render_template('register.html', error="Пароли не совпадают")

        try:
            # Подключение к базе данных
            with db_connect() as conn:
                cursor = conn.cursor()

                # Проверка уникальности email
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                existing_user = cursor.fetchone()

                if existing_user:
                    return render_template('register.html', error="Пользователь с таким email уже существует")

                # Хеширование пароля
                hashed_password = generate_password_hash(password)

                # Вставка нового пользователя
                cursor.execute("""
                    INSERT INTO users (name, email, password_hash, role)
                    VALUES (%s, %s, %s, %s)
                """, (name, email, hashed_password, role))
                conn.commit()

                return redirect(url_for('home'))  # Переход на главную страницу после регистрации

        except Exception as e:
            print(f"[ERROR] Ошибка при выполнении SQL-запроса: {e}")
            return render_template('register.html', error="Ошибка сервера. Попробуйте позже.")

    return render_template('register.html')



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


def role_protected_view(role):
    """
    Декоратор для защиты маршрутов в зависимости от роли пользователя.
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if session.get('role') != role:
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return wrapped
    return decorator


@app.route('/admin_dashboard')
@role_protected_view('Administrator')
def admin_dashboard():
    users = []
    try:
        with db_connect() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT u.id, u.name, u.email, r.name AS role
                FROM users u
                JOIN roles r ON u.role = r.id
            """)
            users = cursor.fetchall()
    except Exception as e:
        print(f"[ERROR] Ошибка при выполнении SQL-запроса: {e}")
        return "Ошибка при загрузке данных", 500

    return render_template('admin_dashboard.html', user_name=session.get('name'), users=users)


@app.route('/dispatcher_dashboard')
def dispatcher_dashboard():
    # Проверка авторизации
    if not session.get('user_id') or session.get('role') != 'Dispatcher':
        return redirect(url_for('login'))

    orders = []
    try:
        # Подключение к базе данных
        with db_connect() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, description , status
                FROM orders
            """)
            orders = cursor.fetchall()
    except Exception as e:
        print(f"[ERROR] Ошибка при выполнении SQL-запроса: {e}")
        return "Ошибка при загрузке данных", 500

    # Передача данных в шаблон
    return render_template('dispatcher_dashboard.html', orders=orders)


@app.route('/specialist_dashboard')
@role_protected_view('Specialist')
def specialist_dashboard():
    return render_template('specialist_dashboard.html', user_name=session.get('name'))


@app.route('/executor_dashboard')
@role_protected_view('Executor')
def executor_dashboard():
    return render_template('executor_dashboard.html', user_name=session.get('name'))


@app.route('/customer_dashboard')
@role_protected_view('Customer')
def customer_dashboard():
    return render_template('customer_dashboard.html', user_name=session.get('name'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
