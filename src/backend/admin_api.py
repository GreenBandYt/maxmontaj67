from flask import Blueprint, render_template, redirect, url_for, session

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/orders', methods=['GET'])
def orders():
    """
    Страница управления заказами для администратора.
    """
    if session.get('role') != 'Administrator':
        return redirect(url_for('home'))

    # Заглушка данных для заказов
    orders = [
        {"id": 1, "description": "Установка оборудования", "status": "Ожидает"},
        {"id": 2, "description": "Ремонт оборудования", "status": "Выполняется"}
    ]
    # Используем корректный путь к шаблону
    return render_template('admin/orders/admin_orders.html', orders=orders)
