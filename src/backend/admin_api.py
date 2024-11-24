from flask import Blueprint, render_template, redirect, url_for, session, request
from utils import db_connect
from utils.validators import is_user_data_complete
import logging

# Логирование
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Создание Blueprint для маршрутов администратора
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ----------------------------------------
# Маршрут: Отображение всех заказов
# ----------------------------------------
@admin_bp.route('/orders', methods=['GET'])
def orders():
    """
    Маршрут для отображения всех заказов.
    """
    if session.get('role') != 'Administrator':  # Проверка прав доступа
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
                    c.name AS customer_name,
                    u.name AS installer_name
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                LEFT JOIN users u ON o.installer_id = u.id
            """)
            orders = cursor.fetchall()

        logging.debug(f"[DEBUG] Загружено заказов: {orders}")
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
    if session.get('role') != 'Administrator':  # Проверка прав доступа
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
    if session.get('role') != 'Administrator':  # Проверка прав доступа
        return redirect(url_for('home'))

    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.name, u.email, r.name AS role, u.created_at
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
@admin_bp.route('/assign_executor/<int:order_id>', methods=['GET', 'POST'])
def assign_executor(order_id):
    """
    Назначение исполнителя для заказа.
    """
    if session.get('role') != 'Administrator':  # Проверка прав доступа
        return redirect(url_for('home'))

    try:
        logging.debug(f"[DEBUG] Открыт маршрут назначения исполнителя для заказа ID: {order_id}")

        with db_connect() as conn:
            cursor = conn.cursor()

            # SQL-запрос для получения списка исполнителей
            cursor.execute("""
                SELECT u.id, u.name, r.name AS role
                FROM users u
                JOIN roles r ON u.role = r.id
                WHERE r.name IN ('Executor', 'Specialist')
            """)
            executors = cursor.fetchall()
            logging.debug(f"[DEBUG] Найдены исполнители: {executors}")

            # Проверка существования заказа
            cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            order = cursor.fetchone()
            if not order:
                logging.error(f"[ERROR] Заказ с ID {order_id} не найден.")
                return "Заказ не найден", 404

            if request.method == 'POST':  # Обработка назначения исполнителя
                executor_id = request.form['executor']
                logging.debug(f"[DEBUG] Назначение исполнителя ID: {executor_id} для заказа ID: {order_id}")

                # Проверяем, существует ли выбранный исполнитель
                cursor.execute("SELECT * FROM users WHERE id = %s", (executor_id,))
                executor = cursor.fetchone()
                if not executor:
                    logging.error(f"[ERROR] Исполнитель с ID {executor_id} не найден.")
                    return "Исполнитель не найден", 404

                # Проверяем, заполнены ли все данные исполнителя
                if not is_user_data_complete(executor):
                    logging.warning(f"[WARNING] У исполнителя с ID {executor_id} неполные данные.")
                    return "Исполнитель не может быть назначен: неполные данные.", 400

                # Обновляем заказ с назначением исполнителя
                cursor.execute("""
                    UPDATE orders
                    SET installer_id = %s, status = 'Выполняется', assigned_at = NOW()
                    WHERE id = %s
                """, (executor_id, order_id))
                conn.commit()
                logging.info(f"[INFO] Исполнитель с ID {executor_id} назначен на заказ ID {order_id}.")
                return redirect(url_for('admin.orders'))

            # Передача данных в шаблон
            return render_template('admin/orders/assign_executor.html', order_id=order_id, executors=executors)

    except Exception as e:
        logging.error(f"[ERROR] Ошибка при назначении исполнителя: {e}")
        return "Ошибка сервера. Попробуйте позже.", 500


# ----------------------------------------
# Маршрут: Снятие исполнителя с заказа
# ----------------------------------------
@admin_bp.route('/remove_executor/<int:order_id>', methods=['POST'])
def remove_executor(order_id):
    """
    Снятие исполнителя с заказа.
    """
    if session.get('role') != 'Administrator':  # Проверка прав доступа
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
    if session.get('role') != 'Administrator':  # Проверка прав доступа
        return redirect(url_for('home'))  # Перенаправление, если пользователь не админ

    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Проверяем существование пользователя
            cursor.execute("""
                SELECT u.id, u.name, u.email, u.phone, u.address, u.passport_data,
                       u.rating, u.role AS role_id, r.name AS role_name
                FROM users u
                JOIN roles r ON u.role = r.id
                WHERE u.id = %s
            """, (user_id,))
            user = cursor.fetchone()
            if not user:
                return "Пользователь не найден", 404

            # Получаем список всех ролей для выбора
            cursor.execute("SELECT id, name FROM roles")
            roles = cursor.fetchall()

            if request.method == 'POST':  # Обработка формы
                # Считываем данные из формы
                name = request.form.get('name')
                phone = request.form.get('phone')
                address = request.form.get('address')
                rating = request.form.get('rating')
                role_id = request.form.get('role')

                # Валидация обязательных полей
                if not all([name, phone, address, rating]):
                    return "Все обязательные поля должны быть заполнены.", 400

                # Проверка диапазона рейтинга
                try:
                    rating = float(rating)
                    if not (0 <= rating <= 5):
                        return "Рейтинг должен быть в диапазоне от 0 до 5.", 400
                except ValueError:
                    return "Рейтинг должен быть числом.", 400

                # Обновление данных пользователя
                cursor.execute("""
                    UPDATE users
                    SET name = %s, phone = %s, address = %s, rating = %s, role = %s
                    WHERE id = %s
                """, (name, phone, address, rating, role_id, user_id))
                conn.commit()

                return redirect(url_for('admin.users'))

            # Передача данных в шаблон
            return render_template('admin/users/admin_user_detail.html', user=user, roles=roles)

    except Exception as e:
        logging.error(f"[ERROR] Ошибка при редактировании пользователя: {e}")
        return "Ошибка сервера. Попробуйте позже.", 500

