from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
from config import SESSION_CONFIG
from utils import db_connect, verify_password, hash_password

# Импортируем Blueprints
from admin_api import admin_bp

# Настройка приложения Flask
app = Flask(__name__)
app.config['SESSION_TYPE'] = SESSION_CONFIG['type']
app.config['SESSION_PERMANENT'] = SESSION_CONFIG['permanent']
app.config['SESSION_FILE_DIR'] = SESSION_CONFIG['file_dir']
Session(app)

# Регистрация Blueprints
app.register_blueprint(admin_bp)

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
                    SELECT u.id, u.password_hash, r.name AS role, u.name
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
                    'Administrator': 'admin.orders',
                    'Dispatcher': 'dispatcher.orders',
                    'Specialist': 'specialist.orders',
                    'Executor': 'executor.orders',
                    'Customer': 'customer.orders',
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


@app.route('/logout')
def logout():
    """
    Выход из системы: очищает сессию и перенаправляет на главную страницу.
    """
    session.clear()  # Очищаем сессию пользователя
    return redirect(url_for('home'))  # Перенаправляем на главную страницу


if __name__ == '__main__':
    # Печатаем зарегистрированные маршруты для отладки
    for rule in app.url_map.iter_rules():
        print(f"Rule: {rule}, Endpoint: {rule.endpoint}")
    app.run(debug=True, host='0.0.0.0')
