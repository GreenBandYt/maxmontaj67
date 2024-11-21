from flask import Blueprint, render_template, session, redirect, url_for

specialist_bp = Blueprint('specialist', __name__, url_prefix='/specialist')

@specialist_bp.route('/orders', methods=['GET'])
def orders():
    # Проверка роли пользователя
    if session.get('role') != 'Specialist':
        return redirect(url_for('home'))

    # Логика загрузки заказов для специалиста
    orders = [
        {"id": 1, "description": "Ремонт оборудования", "status": "Выполняется"},
        {"id": 2, "description": "Установка оборудования", "status": "Завершён"}
    ]
    return render_template('specialist/orders/specialist_orders.html', orders=orders)
