from flask import Blueprint, render_template, session, redirect, url_for

executor_bp = Blueprint('executor', __name__, url_prefix='/executor')

@executor_bp.route('/orders', methods=['GET'])
def orders():
    # Проверка роли пользователя
    if session.get('role') != 'Executor':
        return redirect(url_for('home'))

    # Логика загрузки заказов для исполнителя
    orders = [
        {"id": 1, "description": "Монтаж оборудования", "status": "Ожидает"},
        {"id": 2, "description": "Техническое обслуживание", "status": "Выполняется"}
    ]
    return render_template('executor/orders/executor_orders.html', orders=orders)
