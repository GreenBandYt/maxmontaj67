from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_session import Session
from multiprocessing import Process
import subprocess
import os
from decouple import config  # Добавлен импорт
from config import SESSION_CONFIG
from utils import db_connect, verify_password, hash_password

# Импортируем Blueprints
from admin_api import admin_bp
from customer_api import customer_bp
from dispatcher_api import dispatcher_bp
from executor_api import executor_bp
from specialist_api import specialist_bp
from calendar_api import calendar_bp


# Настройка приложения Flask
app = Flask(__name__)
app.config['SESSION_TYPE'] = SESSION_CONFIG['type']
app.config['SESSION_PERMANENT'] = SESSION_CONFIG['permanent']
app.config['SESSION_FILE_DIR'] = SESSION_CONFIG['file_dir']
Session(app)


# Делаем переменную environment доступной в шаблонах
@app.context_processor
def inject_environment():
    """
    Функция, которая делает переменную environment доступной во всех шаблонах.
    """
    return {'environment': config('FLASK_ENV', default='production')}

# Проверка переменной окружения
print(f"Текущая среда: {config('FLASK_ENV', default='production')}")

# Регистрация Blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(dispatcher_bp)
app.register_blueprint(executor_bp)
app.register_blueprint(specialist_bp)
app.register_blueprint(calendar_bp)

# Глобальные переменные для управления ботом
bot_process = None
bot_running = False  # Флаг состояния бота

# Функция для запуска бота
def run_bot():
    os.system("python3 telegram_bot/bot_runner.py")

@app.route('/bot/start', methods=['POST'])
def start_bot():
    """
    Запуск Telegram-бота как модуля.
    """
    global bot_process, bot_running

    if not bot_running:
        def run_bot():
            subprocess.run(['python3', '-m', 'telegram_bot.bot_runner'])

        bot_process = Process(target=run_bot)
        bot_process.start()
        bot_running = True
        return jsonify({"status": "success", "message": "Бот запущен"}), 200
    else:
        return jsonify({"status": "error", "message": "Бот уже работает"}), 400

@app.route('/bot/stop', methods=['POST'])
def stop_bot():
    """
    Остановка Telegram-бота.
    """
    global bot_process, bot_running

    if bot_running and bot_process is not None:
        bot_process.terminate()
        bot_process.join()
        bot_running = False
        return jsonify({"status": "success", "message": "Бот остановлен"}), 200
    else:
        return jsonify({"status": "error", "message": "Бот не запущен"}), 400


@app.route('/', methods=['GET', 'POST'])
def home():
    """
    Главная страница входа в систему.
    """
    if request.method == 'POST':
        email = request.form.get('email')  # Получаем email из формы
        password = request.form.get('password')  # Получаем пароль из формы

        # Логируем полученные данные
        app.logger.debug(f"Полученные данные: email={email}, password={'*' * len(password) if password else None}")

        try:
            # Подключение к базе данных
            with db_connect() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT u.id, u.email, u.password_hash, r.name AS role, u.name
                    FROM users u
                    JOIN roles r ON u.role = r.id
                    WHERE u.email = %s
                """
                # Логируем выполнение SQL-запроса
                app.logger.debug(f"Выполнение SQL-запроса: {query} с параметром: {email}")
                cursor.execute(query, (email,))
                user = cursor.fetchone()  # Получаем данные пользователя

                if user:
                    # Логируем успешное выполнение запроса
                    # Проверяем, является ли пользователь заблокированным
                    if user['role'] == 'Blocked':
                        app.logger.warning(f"Доступ заблокирован для пользователя: {user['email']}")
                        return render_template('index.html',
                                               error="Ваш доступ заблокирован. Обратитесь к администратору.")

                    app.logger.debug(f"Найден пользователь: {user}")
                else:
                    # Логируем, если пользователь не найден
                    app.logger.warning(f"Пользователь с email {email} не найден.")
                    return render_template('index.html', error="Неверный логин или пароль")

            # Проверяем пароль
            app.logger.debug(f"[DEBUG] Попытка проверки пароля для хэша: {user['password_hash']}")
            if verify_password(password, user['password_hash']):
                # Логируем успешную проверку пароля
                app.logger.info(f"Успешный вход: role={user['role']}, name={user['name']}")

                # Сохраняем данные пользователя в сессии
                session['user_id'] = user['id']
                session['role'] = user['role']
                session['name'] = user['name']

                # Перенаправление в зависимости от роли
                role_redirects = {
                    'admin': 'admin.orders',
                    'dispatcher': 'dispatcher.orders',
                    'specialist': 'specialist.orders',
                    'executor': 'executor.orders',
                    'customer': 'customer.orders',
                }
                return redirect(url_for(role_redirects.get(user['role'], 'home')))
            else:
                # Логируем неудачную проверку пароля
                app.logger.warning("Ошибка проверки пароля: пароль не совпадает")
                return render_template('index.html', error="Неверный логин или пароль")

        except Exception as e:
            # Логируем любую другую ошибку
            app.logger.error(f"Неожиданная ошибка: {e}")
            return render_template('index.html', error="Ошибка сервера. Попробуйте позже.")

    # Если метод GET, отображаем страницу входа
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Страница регистрации нового пользователя.
    """
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        role = request.form['role']
        if password != password_confirm:
            return render_template('register.html', error="Пароли не совпадают")
        try:
            with db_connect() as conn:
                cursor = conn.cursor()
                # Проверка уникальности email
                cursor.execute("SELECT id FROM users WHERE email = %s UNION SELECT id FROM customers WHERE email = %s", (email, email))
                if cursor.fetchone():
                    return render_template('register.html', error="Email уже зарегистрирован")
                # Хеширование пароля
                hashed_password = hash_password(password)
                print(f"[DEBUG] Создан хэш пароля: {hashed_password}")
                # Логика добавления в зависимости от роли
                if role == '5':  # Если роль Customer
                    cursor.execute("""
                        INSERT INTO customers (name, email, password_hash, created_at)
                        VALUES (%s, %s, %s, NOW())
                    """, (name, email, hashed_password))
                    conn.commit()
                    # Установить данные сессии
                    session['user_id'] = cursor.lastrowid
                    session['role'] = 'Customer'
                    session['name'] = name
                    print(f"[DEBUG] Пользователь {name} добавлен в таблицу customers")
                    return redirect(url_for('customer.orders'))
                else:  # Для остальных ролей
                    cursor.execute("""
                        INSERT INTO users (name, email, password_hash, role, created_at)
                        VALUES (%s, %s, %s, %s, NOW())
                    """, (name, email, hashed_password, role))
                    conn.commit()
                    # Установить данные сессии
                    session['user_id'] = cursor.lastrowid
                    session['role'] = role
                    session['name'] = name
                    print(f"[DEBUG] Пользователь {name} добавлен в таблицу users")
                    return redirect(url_for('home'))  # Перенаправление после регистрации
        except Exception as e:
            print(f"[ERROR] Ошибка регистрации: {e}")
            return render_template('register.html', error="Ошибка сервера. Попробуйте позже.")
    return render_template('register.html')


@app.route('/logout')
def logout():
    """
    Выход из системы: очищает сессию и перенаправляет на главную страницу.
    """
    session.clear()  # Очищаем сессию пользователя
    return redirect(url_for('home'))  # Перенаправляем на главную страницу


if __name__ == '__main__':
    # Печатаем зарегистрированные маршруты для отладки
    # for rule in app.url_map.iter_rules():
    #     print(f"Rule: {rule}, Endpoint: {rule.endpoint}")
    app.run(debug=True, host='0.0.0.0')
