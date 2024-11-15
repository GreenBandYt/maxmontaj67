
from flask_mysqldb import MySQL
from flask import Flask, request, jsonify, render_template, redirect, flash, url_for

app = Flask(__name__)
app.secret_key = 'supersecretkey5054'

# Настройка соединения с базой данных
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'greenbandyt'
app.config['MYSQL_PASSWORD'] = 'byv'
app.config['MYSQL_DB'] = 'maxmontaj67'

mysql = MySQL(app)

# Маршрут для создания нового заказчика
@app.route('/api/customers', methods=['POST'])
def create_customer():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Нет данных"}), 400

    try:
        cur = mysql.connection.cursor()
        query = """
            INSERT INTO customers (name, phone, email, address)
            VALUES (%s, %s, %s, %s)
        """
        cur.execute(query, (data['name'], data.get('phone'), data.get('email'), data.get('address')))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Заказчик успешно создан"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Маршрут для создания заказа
@app.route('/api/orders', methods=['POST'])
def create_new_order():
    data = request.form

    if not data:
        flash("Нет данных для создания заказа", "error")
        return redirect(url_for('create_order_page'))

    # Если выбран новый заказчик, создаем его и используем ID для нового заказа
    if data['customer_id'] == 'new':
        try:
            cur = mysql.connection.cursor()
            query = """
                INSERT INTO customers (name, phone, email, address)
                VALUES (%s, %s, %s, %s)
            """
            cur.execute(query, (data['new_customer_name'], data.get('new_customer_phone'), data.get('new_customer_email'), data.get('new_customer_address')))
            mysql.connection.commit()
            customer_id = cur.lastrowid
            cur.close()
        except Exception as e:
            flash(f"Ошибка при создании заказчика: {str(e)}", "error")
            return redirect(url_for('create_order_page'))
    else:
        customer_id = data['customer_id']

    try:
        cur = mysql.connection.cursor()
        query = """
            INSERT INTO orders (customer_id, work_type, address, status)
            VALUES (%s, %s, %s, %s)
        """
        cur.execute(query, (customer_id, data['work_type'], data['address'], 'new'))
        mysql.connection.commit()
        cur.close()
        flash('Заказ успешно создан.', 'success')
        return redirect(url_for('client_dashboard'))
    except Exception as e:
        flash(f"Ошибка при создании заказа: {str(e)}", "error")
        return redirect(url_for('create_order_page'))


# Маршрут для обновления заказа
@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "Нет данных"}), 400

    try:
        cur = mysql.connection.cursor()
        query = """
            UPDATE orders SET status = %s WHERE id = %s
        """
        cur.execute(query, (data['status'], order_id))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Статус заказа обновлен"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Маршрут для назначения монтажника на заказ
@app.route('/api/orders/<int:order_id>/assign', methods=['PUT'])
def assign_order_installer(order_id):
    data = request.get_json()

    if not data or 'installer_id' not in data:
        return jsonify({"error": "Нет данных или не указан installer_id"}), 400

    try:
        cur = mysql.connection.cursor()
        query = """
            UPDATE orders SET installer_id = %s WHERE id = %s
        """
        cur.execute(query, (data['installer_id'], order_id))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Монтажник успешно назначен"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Маршруты для отображения HTML-страниц
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/dispatcher_dashboard')
def dispatcher_dashboard():
    try:
        cur = mysql.connection.cursor()
        query = """
            SELECT id, customer_id, work_type, address, status, installer_id FROM orders
        """
        cur.execute(query)
        orders = cur.fetchall()
        cur.close()
        return render_template('dispatcher_dashboard.html', orders=orders)
    except Exception as e:
        return f"Ошибка при получении данных: {str(e)}", 500

@app.route('/installer_dashboard')
def installer_dashboard():
    try:
        cur = mysql.connection.cursor()
        query = """
            SELECT id, work_type, address FROM orders
            WHERE status = 'new' AND installer_id IS NULL
        """
        cur.execute(query)
        available_orders = cur.fetchall()
        cur.close()

        return render_template('installer_dashboard.html', available_orders=available_orders)
    except Exception as e:
        return f"Ошибка при получении данных: {str(e)}", 500

@app.route('/create_order')
def create_order_page():
    try:
        cur = mysql.connection.cursor()
        query = """
            SELECT id, name FROM customers
        """
        cur.execute(query)
        customers = cur.fetchall()
        cur.close()
        return render_template('create_order.html', customers=customers)
    except Exception as e:
        return f"Ошибка при получении данных: {str(e)}", 500

@app.route('/my_orders')
def my_orders():
    try:
        cur = mysql.connection.cursor()
        query = """
            SELECT id, work_type, address, status FROM orders
            WHERE installer_id = %s
        """
        installer_id = 1  # Замените на актуальный идентификатор пользователя
        cur.execute(query, (installer_id,))
        orders = cur.fetchall()
        cur.close()
        return render_template('my_orders.html', orders=orders)
    except Exception as e:
        return f"Ошибка при получении данных: {str(e)}", 500

@app.route('/assign_installer/<int:order_id>')
def assign_installer_page(order_id):
    try:
        cur = mysql.connection.cursor()
        query = """
            SELECT id, name FROM installers
        """
        cur.execute(query)
        installers = cur.fetchall()
        cur.close()
        return render_template('assign_installer.html', order_id=order_id, installers=installers)
    except Exception as e:
        return f"Ошибка при получении данных: {str(e)}", 500

@app.route('/available_orders')
def available_orders():
    return render_template('available_orders.html')

@app.route('/client_dashboard')
def client_dashboard():
    return render_template('client_dashboard.html')

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/view_feedback')
def view_feedback():
    return render_template('view_feedback.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
