# config.py

DATABASE_CONFIG = {
    'host': 'localhost',
    'user': 'greenbandyt',
    'password': 'byv',
    'database': 'maxmontaj67_db'
}

SESSION_CONFIG = {
    'type': 'filesystem',
    'permanent': False,
    'file_dir': '/tmp/flask_session'
}


SECRET_KEY = 'supersecretkey5054'