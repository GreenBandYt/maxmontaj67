from flask import Blueprint, render_template, session, redirect, url_for

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

@customer_bp.route('/orders', methods=['GET'])
def orders():
    # Проверка роли пользователя
    if session.get('role') != 'Customer':
        return redirect(url_for('home'))

    # Логика загрузки заказов для заказчика
    orders = [
        {"id": 1, "description": "Установка оборудования", "status": "Ожидает"},
        {"id": 2, "description": "Ремонт системы вентиляции", "status": "Завершён"}
    ]
    return render_template('customer/orders/customer_orders.html', orders=orders)
