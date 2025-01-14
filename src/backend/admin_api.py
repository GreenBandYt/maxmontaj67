from flask import Blueprint, render_template, redirect, url_for, session, request, flash, jsonify
from utils import db_connect
from utils.validators import is_user_data_complete
import logging
import os
from datetime import datetime



# Логирование
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Создание Blueprint для маршрутов администратора
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Путь для хранения загруженных фото
PHOTO_UPLOAD_FOLDER = 'static/uploads/photos/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Проверка разрешенных расширений
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ----------------------------------------
# Маршрут: Отображение всех заказов
# ----------------------------------------
@admin_bp.route('/orders', methods=['GET'])
def orders():
    """
    Маршрут для отображения всех заказов.
    """
    if session.get('role') != 'admin':  # Проверка прав доступа
        return redirect(url_for('home'))  # Перенаправление на главную страницу, если роль не админ

    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    o.id,
                    o.description,
                    o.status,
                    o.created_at,
                    o.updated_at,
                    o.assigned_at,
                    o.montage_date,
                    c.name AS customer_name,
                    u.name AS installer_name
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                LEFT JOIN users u ON o.installer_id = u.id
            """)
            orders = cursor.fetchall()

        #logging.debug(f"[DEBUG] Загружено заказов: {orders}")
        return render_template('admin/orders/admin_orders.html', orders=orders)

    except Exception as e:
        logging.error(f"[ERROR] Ошибка загрузки заказов: {e}")
        return "Ошибка сервера. Попробуйте позже.", 500



# ----------------------------------------
# Маршрут: Отображение всех заказчиков
# ----------------------------------------
@admin_bp.route('/customers', methods=['GET'])
def customers():
    """
    Маршрут для отображения списка заказчиков.
    """
    if session.get('role') != 'admin':  # Проверка прав доступа
        return redirect(url_for('home'))

    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, email, phone, address, created_at
                FROM customers
            """)
            customers = cursor.fetchall()

        logging.debug(f"[DEBUG] Загружено заказчиков: {customers}")
        return render_template('admin/users/admin_customers.html', customers=customers)

    except Exception as e:
        logging.error(f"[ERROR] Ошибка загрузки заказчиков: {e}")
        return "Ошибка сервера. Попробуйте позже.", 500


# ----------------------------------------
# Маршрут: Отображение всех пользователей
# ----------------------------------------
@admin_bp.route('/users', methods=['GET'])
def users():
    """
    Маршрут для отображения списка пользователей.
    """
    if session.get('role') != 'admin':  # Проверка прав доступа
        return redirect(url_for('home'))

    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.name, u.email, r.name AS role, u.created_at, u.is_profile_complete
                FROM users u
                JOIN roles r ON u.role = r.id
            """)
            users = cursor.fetchall()

        logging.debug(f"[DEBUG] Загружено пользователей: {users}")
        return render_template('admin/users/admin_users.html', users=users)

    except Exception as e:
        logging.error(f"[ERROR] Ошибка загрузки пользователей: {e}")
        return "Ошибка сервера. Попробуйте позже.", 500

# ----------------------------------------
# Маршрут: Назначение исполнителя заказа
# ----------------------------------------
@admin_bp.route('/assign_installer/<int:order_id>', methods=['GET', 'POST'])
def assign_installer(order_id):
    """
    Назначение исполнителя для заказа.
    """
    if session.get('role') != 'admin':  # Проверка прав доступа
        return redirect(url_for('home'))

    try:
        logging.debug(f"[DEBUG] Открыт маршрут назначения исполнителя для заказа ID: {order_id}")

        with db_connect() as conn:
            cursor = conn.cursor()

            # SQL-запрос для получения списка исполнителей
            cursor.execute("""
                SELECT u.id, u.name, u.is_profile_complete, r.name AS role
                FROM users u
                JOIN roles r ON u.role = r.id
                WHERE r.name IN ('executor', 'specialist') AND u.is_profile_complete = TRUE
            """)
            installers = cursor.fetchall()
            logging.debug(f"[DEBUG] Найдены исполнители: {installers}")

            # Запрос для получения информации о заказе
            cursor.execute("""
                SELECT o.id, o.description, o.status, o.created_at, o.installer_id, 
                       c.name AS customer_name
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                WHERE o.id = %s
            """, (order_id,))
            order = cursor.fetchone()

            if not order:
                logging.error(f"[ERROR] Заказ с ID {order_id} не найден.")
                return "Заказ не найден", 404

            # Получение текущего исполнителя, если он назначен
            current_installer = None
            if order['installer_id']:
                cursor.execute("SELECT id, name FROM users WHERE id = %s", (order['installer_id'],))
                current_installer = cursor.fetchone()
                logging.debug(f"[DEBUG] Текущий исполнитель: {current_installer}")

            if request.method == 'POST':  # Обработка назначения исполнителя
                installer_id = request.form['installer']

                logging.debug(f"[DEBUG] Назначение исполнителя ID: {installer_id} для заказа ID: {order_id}")

                # Проверяем, существует ли выбранный исполнитель
                cursor.execute("SELECT * FROM users WHERE id = %s", (installer_id,))
                installer = cursor.fetchone()
                if not installer:
                    logging.error(f"[ERROR] Исполнитель с ID {installer_id} не найден.")
                    return "Исполнитель не найден", 404

                # Проверяем, заполнены ли все данные исполнителя
                if not installer['is_profile_complete']:
                    logging.warning(f"[WARNING] У исполнителя с ID {installer_id} неполные данные.")
                    return "Исполнитель не может быть назначен: неполные данные.", 400

                # Обновляем заказ с назначением исполнителя
                cursor.execute("""
                    UPDATE orders
                    SET installer_id = %s, status = 'Выполняется', assigned_at = NOW()
                    WHERE id = %s
                """, (installer_id, order_id))
                conn.commit()
                logging.info(f"[INFO] Исполнитель с ID {installer_id} назначен на заказ ID {order_id}.")
                return redirect(url_for('admin.orders'))

            # Передача данных в шаблон
            return render_template(
                'admin/orders/assign_installer.html',
                order_id=order_id,
                order=order,
                installers=installers,
                current_installer=current_installer
            )

    except Exception as e:
        logging.error(f"[ERROR] Ошибка при назначении исполнителя: {e}")
        return "Ошибка сервера. Попробуйте позже.", 500

# ----------------------------------------
# API: Загрузка данных об исполнителе
# ----------------------------------------
@admin_bp.route('/get_installer_info/<int:installer_id>', methods=['GET'])
def get_installer_info(installer_id):
    """
    Возвращает информацию об исполнителе.
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Запрос для получения данных исполнителя
            cursor.execute("""
                SELECT id, name, role, phone, address, rating
                FROM users
                WHERE id = %s
            """, (installer_id,))
            installer = cursor.fetchone()

            if not installer:
                return jsonify({"error": "Исполнитель не найден"}), 404

            return jsonify(installer)
    except Exception as e:
        logging.error(f"[ERROR] Ошибка при загрузке данных об исполнителе: {e}")
        return jsonify({"error": "Ошибка сервера"}), 500


# ----------------------------------------
# Маршрут: Снятие исполнителя с заказа
# ----------------------------------------
@admin_bp.route('/remove_installer/<int:order_id>', methods=['POST'])
def remove_installer(order_id):
    """
    Снятие исполнителя с заказа.
    """
    if session.get('role') != 'admin':  # Проверка прав доступа
        return redirect(url_for('home'))

    try:
        logging.debug(f"[DEBUG] Снятие исполнителя с заказа ID: {order_id}")

        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE orders
                SET installer_id = NULL, status = 'Ожидает', assigned_at = NULL
                WHERE id = %s
            """, (order_id,))
            conn.commit()
            logging.info(f"[INFO] Исполнитель снят с заказа ID {order_id}.")

        return redirect(url_for('admin.orders'))

    except Exception as e:
        logging.error(f"[ERROR] Ошибка при снятии исполнителя: {e}")
        return "Ошибка сервера. Попробуйте позже.", 500


# ----------------------------------------
# Маршрут: Редактирование данных пользователя
# ----------------------------------------
@admin_bp.route('/users/<int:user_id>', methods=['GET', 'POST'])
def user_details(user_id):
    """
    Маршрут для просмотра и редактирования данных пользователя.
    """
    if session.get('role') != 'admin':  # Проверка прав доступа
        return redirect(url_for('home'))  # Перенаправление, если пользователь не админ

    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Получаем данные пользователя
            cursor.execute("""
                SELECT u.id, u.name, u.email, u.phone, u.address, u.rating, 
                       u.role AS role_id, r.name AS role_name, u.photo_path, 
                       u.passport_issue_date, u.passport_series, u.passport_number, u.passport_issued_by, 
                       u.is_profile_complete 
                FROM users u
                JOIN roles r ON u.role = r.id
                WHERE u.id = %s
            """, (user_id,))
            user = cursor.fetchone()
            if not user:
                return "Пользователь не найден", 404

            # Преобразование данных паспорта (если требуется)
            user['passport_issue_date'] = user['passport_issue_date'] or ''

            # Получаем список всех ролей
            cursor.execute("SELECT id, name FROM roles")
            roles = cursor.fetchall()

            if request.method == 'POST':  # Обработка формы редактирования
                name = request.form.get('name')
                phone = request.form.get('phone')
                address = request.form.get('address')
                rating = request.form.get('rating')
                role_id = request.form.get('role')

                # Валидация обязательных полей
                if not all([name, phone, address, rating, role_id]):
                    flash('Все обязательные поля должны быть заполнены.', 'error')
                    return redirect(url_for('admin.user_details', user_id=user_id))

                # Проверка диапазона рейтинга
                try:
                    rating = float(rating)
                    if not (0 <= rating <= 5):
                        flash('Рейтинг должен быть в диапазоне от 0 до 5.', 'error')
                        return redirect(url_for('admin.user_details', user_id=user_id))
                except ValueError:
                    flash('Рейтинг должен быть числом.', 'error')
                    return redirect(url_for('admin.user_details', user_id=user_id))

                # Обновление данных пользователя в базе
                cursor.execute("""
                    UPDATE users
                    SET name = %s, phone = %s, address = %s, rating = %s, role = %s
                    WHERE id = %s
                """, (name, phone, address, rating, role_id, user_id))

                # Проверка на полноту данных
                is_profile_complete = all([name, phone, address])
                cursor.execute("""
                    UPDATE users
                    SET is_profile_complete = %s
                    WHERE id = %s
                """, (is_profile_complete, user_id))

                conn.commit()

                flash('Данные пользователя успешно обновлены.', 'success')
                return redirect(url_for('admin.users'))

            # Передача данных пользователя в шаблон
            logging.debug(f"[DEBUG] Данные пользователя для шаблона: {user}")
            return render_template('admin/users/admin_user_detail.html', user=user, roles=roles)

    except Exception as e:
        logging.error(f"[ERROR] Ошибка при редактировании пользователя ID {user_id}: {e}")
        return "Ошибка сервера. Попробуйте позже.", 500

# ----------------------------------------
# Маршрут: Загрузка фото пользователя
# ----------------------------------------
@admin_bp.route('/users/<int:user_id>/upload_photo', methods=['POST'])
def upload_photo(user_id):
    """
    Маршрут для загрузки или обновления фото пользователя.
    """
    if session.get('role') != 'admin':  # Проверка прав доступа
        return redirect(url_for('home'))

    try:
        # Проверяем, был ли файл загружен
        if 'photo' not in request.files:
            flash('Файл не выбран.', 'error')
            return redirect(url_for('admin.user_details', user_id=user_id))

        file = request.files['photo']

        if file.filename == '':
            flash('Файл не выбран.', 'error')
            return redirect(url_for('admin.user_details', user_id=user_id))

        if file and allowed_file(file.filename):
            # Формируем имя файла и путь
            filename = f"user_{user_id}.jpg"
            filepath = os.path.join('static/images', filename)

            # Сохраняем файл
            file.save(filepath)
            logging.info(f"[INFO] Фото пользователя ID {user_id} успешно загружено: {filepath}")

            # Обновляем путь к фото в базе данных
            relative_path = f"images/{filename}"
            with db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users
                    SET photo_path = %s
                    WHERE id = %s
                """, (relative_path, user_id))
                conn.commit()

            flash('Фото успешно обновлено.', 'success')
            return redirect(url_for('admin.user_details', user_id=user_id))
        else:
            flash('Недопустимый формат файла. Разрешены только PNG, JPG, JPEG.', 'error')
            return redirect(url_for('admin.user_details', user_id=user_id))

    except Exception as e:
        logging.error(f"[ERROR] Ошибка при загрузке фото для пользователя ID {user_id}: {e}")
        return "Ошибка сервера. Попробуйте позже.", 500


@admin_bp.route('/users/<int:user_id>/update_passport', methods=['POST'])
def update_passport_details(user_id):
    """
    Маршрут для обновления паспортных данных пользователя.
    """
    if session.get('role') != 'admin':  # Проверка прав доступа
        return redirect(url_for('home'))  # Перенаправление, если пользователь не администратор

    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Проверяем существование пользователя
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return "Пользователь не найден", 404

            # Получение данных из формы
            passport_series = request.form.get('passport_series')
            passport_number = request.form.get('passport_number')
            passport_issue_date = request.form.get('passport_issue_date')
            passport_issued_by = request.form.get('passport_issued_by')

            # Валидация данных
            if not (passport_series and passport_number and passport_issue_date and passport_issued_by):
                flash('Все поля паспортных данных должны быть заполнены.', 'error')
                return redirect(url_for('admin.user_details', user_id=user_id))

            if not passport_series.isdigit() or len(passport_series) != 4:
                flash('Серия паспорта должна содержать 4 цифры.', 'error')
                return redirect(url_for('admin.user_details', user_id=user_id))

            if not passport_number.isdigit() or len(passport_number) != 6:
                flash('Номер паспорта должен содержать 6 цифр.', 'error')
                return redirect(url_for('admin.user_details', user_id=user_id))

            # Проверка и преобразование формата даты
            try:
                formatted_date = datetime.strptime(passport_issue_date, '%d.%m.%Y').strftime('%d.%m.%Y')
            except ValueError:
                flash('Дата выдачи паспорта должна быть в формате ДД.ММ.ГГГГ.', 'error')
                return redirect(url_for('admin.user_details', user_id=user_id))

            # Обновление данных в базе
            cursor.execute("""
                UPDATE users
                SET passport_series = %s,
                    passport_number = %s,
                    passport_issue_date = %s,
                    passport_issued_by = %s
                WHERE id = %s
            """, (passport_series, passport_number, formatted_date, passport_issued_by, user_id))

            # Проверка заполненности всех данных пользователя
            cursor.execute("""
                SELECT phone, address, passport_series, passport_number, passport_issue_date, passport_issued_by
                FROM users
                WHERE id = %s
            """, (user_id,))
            updated_user = cursor.fetchone()

            is_complete = all(updated_user.values())  # Проверяем, что все данные заполнены
            cursor.execute("""
                UPDATE users
                SET is_profile_complete = %s
                WHERE id = %s
            """, (is_complete, user_id)) 

            conn.commit()
            flash('Паспортные данные успешно обновлены.', 'success')
            return redirect(url_for('admin.user_details', user_id=user_id))

    except Exception as e:
        logging.error(f"[ERROR] Ошибка при обновлении паспортных данных для пользователя ID {user_id}: {e}")
        return "Ошибка сервера. Попробуйте позже.", 500


# ----------------------------------------
# Маршрут: Отображение деталей заказа
# ----------------------------------------
@admin_bp.route('/orders/<int:order_id>', methods=['GET', 'POST'])
def order_details(order_id):
    """
    Маршрут для отображения и редактирования деталей заказа.
    """
    if session.get('role') != 'admin':  # Проверка прав доступа
        return redirect(url_for('home'))  # Перенаправление, если пользователь не администратор

    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            if request.method == 'POST':  # Обработка обновления данных заказа
                description = request.form.get('description')
                status = request.form.get('status')

                # Обработка и преобразование даты монтажа
                montage_date = request.form.get('montage_date') or None
                if montage_date:
                    try:
                        montage_date = datetime.strptime(montage_date, '%Y-%m-%d').date()
                    except ValueError:
                        flash('Дата монтажа указана в некорректном формате.', 'error')
                        montage_date = None

                # Обработка крайнего срока
                deadline_at = request.form.get('deadline_at') or None
                if deadline_at:
                    try:
                        deadline_at = datetime.strptime(deadline_at, '%Y-%m-%d').date()
                    except ValueError:
                        flash('Крайний срок указан в некорректном формате.', 'error')
                        deadline_at = None

                # Обработка даты завершения
                completed_at = request.form.get('completed_at') or None
                if completed_at:
                    try:
                        completed_at = datetime.strptime(completed_at, '%Y-%m-%d').date()
                    except ValueError:
                        flash('Дата завершения указана в некорректном формате.', 'error')
                        completed_at = None

                # Обновляем данные в базе
                cursor.execute("""
                    UPDATE orders
                    SET description = %s, status = %s, montage_date = %s,
                        deadline_at = %s, completed_at = %s
                    WHERE id = %s
                """, (description, status, montage_date, deadline_at, completed_at, order_id))
                conn.commit()

                flash('Данные заказа успешно обновлены.', 'success')
                return redirect(url_for('admin.order_details', order_id=order_id))

            # Получение данных заказа
            cursor.execute("""
                SELECT o.id, o.description, o.status, o.created_at, o.updated_at,
                       o.assigned_at, o.montage_date, o.deadline_at, o.completed_at,
                       c.name AS customer_name, c.phone AS customer_phone, c.address AS customer_address,
                       u.name AS installer_name
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                LEFT JOIN users u ON o.installer_id = u.id
                WHERE o.id = %s
            """, (order_id,))
            order = cursor.fetchone()

            if not order:
                return "Заказ не найден", 404

        return render_template('admin/orders/admin_orders_detail.html', order=order)

    except Exception as e:
        logging.error(f"[ERROR] Ошибка при загрузке или обновлении заказа ID {order_id}: {e}")
        return "Ошибка сервера. Попробуйте позже.", 500
# ----------------------------------------
# Маршрут: Завершение заказа
# ----------------------------------------
@admin_bp.route('/orders/<int:order_id>/complete', methods=['POST'])
def order_complete(order_id):
    """
    Завершение заказа: обновление статуса и даты завершения.
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Проверка существования заказа
            cursor.execute("SELECT id FROM orders WHERE id = %s", (order_id,))
            order = cursor.fetchone()
            if not order:
                flash('Заказ не найден.', 'error')
                return redirect(url_for('admin.order_details', order_id=order_id))

            # Обновление статуса и даты завершения
            cursor.execute("""
                UPDATE orders
                SET status = 'Завершён', completed_at = NOW()
                WHERE id = %s
            """, (order_id,))
            conn.commit()

        flash('Заказ успешно завершён.', 'success')
        return redirect(url_for('admin.order_details', order_id=order_id))  # Перенаправление на ту же страницу
    except Exception as e:
        logging.error(f"Ошибка завершения заказа ID {order_id}: {e}")
        flash('Ошибка при завершении заказа.', 'error')
        return redirect(url_for('admin.order_details', order_id=order_id))


# ----------------------------------------
# Маршрут: Универсальный календарь
# ----------------------------------------

@admin_bp.route('/calendar', methods=['GET'])
def calendar_view():
    """
    Отображение универсального календаря.
    """
    mode = request.args.get('mode', 'executor')  # "executor" или "analytics"
    executor_id = request.args.get('executor_id')  # ID исполнителя, если mode=executor
    return render_template('calendar.html', mode=mode, executor_id=executor_id)

# ----------------------------------------
# Маршрут: Информация об исполнителе
# ----------------------------------------

@admin_bp.route('/installer/info', methods=['GET'])
def get_installer_info():
    installer_id = request.args.get('installer_id')
    if not installer_id:
        return jsonify({'error': 'Installer ID is required'}), 400

    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            # Исправленный SQL-запрос
            query = """
                SELECT u.id, u.name, r.name AS role, COUNT(o.id) AS tasks
                FROM users u
                JOIN roles r ON u.role = r.id  -- Исправлено role_id → role
                LEFT JOIN orders o ON u.id = o.installer_id
                WHERE u.id = %s AND r.name IN ('executor', 'specialist')
            """
            logging.debug(f"[DEBUG] Выполнение SQL-запроса: {query} с параметром {installer_id}")
            cursor.execute(query, (installer_id,))
            installer = cursor.fetchone()

            if not installer:
                logging.warning(f"[WARNING] Исполнитель с ID {installer_id} не найден.")
                return jsonify({'error': 'Installer not found'}), 404

            logging.debug(f"[DEBUG] Найден исполнитель: {installer}")
            return jsonify({
                'id': installer['id'],
                'name': installer['name'],
                'role': installer['role'],
                'tasks': installer['tasks']
            })

    except Exception as e:
        logging.error(f"Ошибка при загрузке информации об исполнителе: {e}")
        return jsonify({'error': 'Server error'}), 500


# ----------------------------------------
# Маршрут: Календарь заказов
# ----------------------------------------
@admin_bp.route('/orders_calendar', methods=['GET'])
def orders_calendar():
    """
    Маршрут для отображения большого календаря заказов.
    """
    if session.get('role') != 'admin':  # Проверка прав доступа
        return redirect(url_for('home'))  # Перенаправление для неадминистраторов

    try:
        # Логирование успешной загрузки
        logging.info("Открыт маршрут для большого календаря заказов")
        return render_template('admin/orders/admin_order_calendar.html')
    except Exception as e:
        logging.error(f"Ошибка загрузки большого календаря заказов: {e}")
        return "Ошибка сервера. Попробуйте позже.", 500


# ----------------------------------------
# Маршрут: Календарь пользователей
# ----------------------------------------
@admin_bp.route('/users_calendar', methods=['GET'])
def users_calendar():
    """
    Маршрут для отображения календаря пользователей.
    """
    if session.get('role') != 'admin':  # Проверка прав доступа
        return redirect(url_for('home'))  # Перенаправление для неадминистраторов

    try:
        # Логирование успешной загрузки
        logging.info("Открыт маршрут для календаря пользователей")
        return render_template('admin/orders/admin_user_calendar.html')
    except Exception as e:
        logging.error(f"Ошибка загрузки календаря пользователей: {e}")
        return "Ошибка сервера. Попробуйте позже.", 500

# ----------------------------------------
# API: Данные для календаря заказов
# ----------------------------------------
@admin_bp.route('/calendar/orders_data', methods=['GET'])
def calendar_orders_data():
    """
    API для получения данных всех заказов для отображения в календаре.
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Получение всех заказов с монтажной датой
            query = """
                SELECT id, description AS title, montage_date AS start
                FROM orders
                WHERE montage_date IS NOT NULL
            """
            cursor.execute(query)
            orders = cursor.fetchall()

            # Форматируем данные для календаря
            events = [
                {
                    "id": order["id"],
                    "title": order["title"],
                    "start": order["start"].strftime('%Y-%m-%d') if order["start"] else None
                }
                for order in orders
            ]

            return jsonify(events)

    except Exception as e:
        logging.error(f"Ошибка при загрузке данных календаря заказов: {e}")
        return jsonify([]), 500


# ----------------------------------------
# API: Данные для календаря пользователей
# ----------------------------------------
@admin_bp.route('/calendar/users_data', methods=['GET'])
def calendar_users_data():
    """
    API для получения данных всех исполнителей для отображения в календаре.
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Получение уникальных исполнителей из заказов
            query = """
                SELECT DISTINCT installer_id AS id, 
                                CONCAT('Исполнитель: ', installer_id) AS title,
                                montage_date AS start
                FROM orders
                WHERE installer_id IS NOT NULL AND montage_date IS NOT NULL
            """
            cursor.execute(query)
            installers = cursor.fetchall()

            # Форматируем данные для календаря
            events = [
                {
                    "id": installer["id"],
                    "title": installer["title"],
                    "start": installer["start"].strftime('%Y-%m-%d') if installer["start"] else None
                }
                for installer in installers
            ]

            return jsonify(events)

    except Exception as e:
        logging.error(f"Ошибка при загрузке данных календаря пользователей: {e}")
        return jsonify([]), 500
