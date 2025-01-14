from flask import Blueprint, jsonify, request
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
