
from decouple import config

app.config['MYSQL_HOST'] = config('MYSQL_HOST')
app.config['MYSQL_USER'] = config('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = config('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = config('MYSQL_DB')



from flask import Flask, render_template, request
from flask_mysqldb import MySQL

app = Flask(__name__)

# Настройка соединения с базой данных
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'greenbandyt'
app.config['MYSQL_PASSWORD'] = 'byv'
app.config['MYSQL_DB'] = 'maxmontaj67'

# Создаем экземпляр подключения к MySQL
mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('index.html')

# Пример маршрута для добавления пользователя (дополнительно)
@app.route('/add_user', methods=['POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)", (username, email, password, role))
        mysql.connection.commit()
        cur.close()
        return 'Пользователь добавлен успешно'

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
