from flask import Blueprint, render_template, redirect, url_for, session
from utils import db_connect
from flask import request

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/orders', methods=['GET'])
def orders():
    """
    Маршрут для отображения всех заказов с полным набором данных.
    """
    # Проверка роли пользователя
    if session.get('role') != 'Administrator':
        return redirect(url_for('home'))

    try:
        # Подключение к базе данных
        with db_connect() as conn:
            cursor = conn.cursor(dictionary=True)
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
            orders = cursor.fetchall()  # Получение всех данных из таблицы orders

        # Передача данных в шаблон
        return render_template('admin/orders/admin_orders.html', orders=orders)

    except Exception as e:
        print(f"[ERROR] Ошибка при загрузке заказов: {e}")
        return "Ошибка сервера. Попробуйте позже.", 500

@admin_bp.route('/users', methods=['GET'])
def users():
    # Проверка роли пользователя
    if session.get('role') != 'Administrator':
        return redirect(url_for('home'))

    try:
        with db_connect() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT u.id, u.name, u.email, r.name AS role, u.created_at
                FROM users u
                JOIN roles r ON u.role = r.id
            """)
            users = cursor.fetchall()
            print(f"[DEBUG] Загружено пользователей: {users}")
    except Exception as e:
        print(f"[ERROR] Ошибка при загрузке пользователей: {e}")
        return "Ошибка при загрузке данных", 500

    # Передача данных в шаблон
    return render_template('admin/users/admin_users.html', users=users)

@admin_bp.route('/customers', methods=['GET'])
def customers():
    """
    Маршрут для отображения списка заказчиков.
    """
    if session.get('role') != 'Administrator':
        return redirect(url_for('home'))

    try:
        with db_connect() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, name, email, phone, address, created_at
                FROM customers
            """)
            customers = cursor.fetchall()
    except Exception as e:
        print(f"[ERROR] Ошибка при загрузке заказчиков: {e}")
        return "Ошибка при загрузке данных", 500

    # Передача данных в шаблон
    return render_template('admin/users/admin_customers.html', customers=customers)


@admin_bp.route('/assign_executor/<int:order_id>', methods=['GET', 'POST'])
def assign_executor(order_id):
    """
    Назначить исполнителя для заказа.
    """
    if request.method == 'POST':
        executor_id = request.form.get('executor_id')  # ID выбранного исполнителя
        try:
            with db_connect() as conn:
                cursor = conn.cursor()

                # Проверяем, существует ли заказ
                cursor.execute("SELECT id FROM orders WHERE id = %s", (order_id,))
                order = cursor.fetchone()
                if not order:
                    return "Заказ не найден", 404

                # Назначаем исполнителя
                cursor.execute("""
                    UPDATE orders
                    SET installer_id = %s, status = 'Выполняется', assigned_at = NOW()
                    WHERE id = %s
                """, (executor_id, order_id))
                conn.commit()
                print("[DEBUG] Исполнитель успешно назначен.")
                return redirect(url_for('admin.orders'))  # Возврат к списку заказов

        except Exception as e:
            print(f"[ERROR] Ошибка назначения исполнителя: {e}")
            return "Ошибка сервера. Попробуйте позже.", 500

    # Если GET-запрос, отображаем список доступных исполнителей
    executors = []
    try:
        with db_connect() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, name 
                FROM users 
                WHERE role IN (
                    SELECT id FROM roles WHERE name IN ('Executor', 'Specialist')
                )
            """)
            executors = cursor.fetchall()
    except Exception as e:
        print(f"[ERROR] Ошибка загрузки списка исполнителей: {e}")
        return "Ошибка сервера. Попробуйте позже.", 500

    return render_template('admin/orders/assign_executor.html', order_id=order_id, executors=executors)

