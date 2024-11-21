from flask import Blueprint, render_template, redirect, url_for, session

dispatcher_bp = Blueprint('dispatcher', __name__, url_prefix='/dispatcher')

@dispatcher_bp.route('/orders', methods=['GET'])
def orders():
    """
    Страница с заказами для диспетчера.
    """
    # Проверка роли пользователя
    if session.get('role') != 'Dispatcher':
        return redirect(url_for('home'))

    # Заглушка для данных заказов
    orders = [
        {"id": 1, "description": "Установка оборудования", "status": "Ожидает"},
        {"id": 2, "description": "Ремонт оборудования", "status": "Выполняется"}
    ]
    return render_template('dispatcher/orders/dispatcher_orders.html', orders=orders)
