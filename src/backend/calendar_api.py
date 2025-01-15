from flask import Blueprint, jsonify, request, render_template
from utils import db_connect
from pymysql.cursors import DictCursor  # Убедитесь, что DictCursor подключен

calendar_bp = Blueprint('calendar', __name__, url_prefix='/calendar')

@calendar_bp.route('/data', methods=['GET'])
def get_calendar_data():
    mode = request.args.get('mode', 'installer')  # installer/analytics
    installer_id = request.args.get('installer_id')  # ID исполнителя

    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Запрос для занятости исполнителя
            if mode == 'installer' and installer_id:
                query = """
                    SELECT id, description AS title,
                           IFNULL(montage_date, CURDATE()) AS start
                    FROM orders
                    WHERE installer_id = %s
                """
                cursor.execute(query, (installer_id,))
                tasks = cursor.fetchall()

                # Отладка: вывод задач
                print(f"Полученные задачи: {tasks}")
            else:
                tasks = []

            # Преобразование данных в JSON
            events = [
                {
                    "id": task["id"],
                    "title": task["title"],
                    "start": task["start"].strftime('%Y-%m-%d') if task["start"] else None
                }
                for task in tasks
            ]

            # Отладка: вывод событий
            print(f"События для календаря: {events}")

            return jsonify(events)

    except Exception as e:
        print(f"Ошибка при обработке данных: {e}")
        return jsonify([])


@calendar_bp.route('/large', methods=['GET'])
def large_calendar():
    """
    Рендер большого календаря для отображения всех заказов.
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor(DictCursor)

            # Получение всех заказов с датой монтажа
            query = """
                SELECT id, description, montage_date AS start, installer_id
                FROM orders
                WHERE montage_date IS NOT NULL
            """
            cursor.execute(query)
            tasks = cursor.fetchall()

            # Форматирование данных для FullCalendar
            events = [
                {
                    "id": task["id"],
                    "title": f"Заказ #{task['id']}: {task['description']}",
                    "start": task["start"].strftime('%Y-%m-%d') if task["start"] else None,
                    "installer": task["installer_id"]
                }
                for task in tasks
            ]

            return render_template('calendar_large.html', events=events)

    except Exception as e:
        print(f"Ошибка при загрузке большого календаря: {e}")
        return "Ошибка сервера. Попробуйте позже.", 500

# ----------------------------------------
# API: Данные для календаря заказов
# ----------------------------------------
@calendar_bp.route('/orders_data', methods=['GET'])
def calendar_orders_data():
    """
    API для получения данных всех заказов для отображения в календаре.
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor(DictCursor)

            # Получение всех заказов с монтажной датой
            query = """
                SELECT id, description AS title, montage_date AS start
                FROM orders
                WHERE montage_date IS NOT NULL
            """
            cursor.execute(query)
            orders = cursor.fetchall()

            # Форматирование данных для FullCalendar
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
        print(f"Ошибка при загрузке данных календаря заказов: {e}")
        return jsonify([]), 500


# ----------------------------------------
# API: Данные для календаря пользователей
# ----------------------------------------
@calendar_bp.route('/users_data', methods=['GET'])
def calendar_users_data():
    """
    API для получения данных всех исполнителей для отображения в календаре.
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor(DictCursor)

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

            # Форматирование данных для FullCalendar
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
        print(f"Ошибка при загрузке данных календаря пользователей: {e}")
        return jsonify([]), 500