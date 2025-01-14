from flask import Blueprint, render_template, session, redirect, url_for
from utils import db_connect

specialist_bp = Blueprint('specialist', __name__, url_prefix='/specialist')

@specialist_bp.route('/orders', methods=['GET'])
def orders():
    # Проверка роли пользователя
    if session.get('role') != 'specialist':
        return redirect(url_for('home'))

    user_id = session.get('user_id')  # ID текущего пользователя
    if not user_id:
        return redirect(url_for('home'))  # Если ID отсутствует, вернуть на главную

    # Подключение к базе данных
    connection = db_connect()
    cursor = connection.cursor()

    # Обновленный запрос с добавлением всех необходимых полей
    cursor.execute("""
        SELECT id, description, status, created_at, updated_at, deadline_at, montage_date
        FROM orders
        WHERE installer_id = %s
    """, (user_id,))
    orders = cursor.fetchall()

    connection.close()

    # Отображение шаблона с заказами
    return render_template('specialist/orders/specialist_orders.html', orders=orders)
