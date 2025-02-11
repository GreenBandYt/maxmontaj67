# states.py

# Словарь начальных состояний для каждой роли
INITIAL_STATES = {
    "guest": "guest_idle",
    "dispatcher": "dispatcher_idle",
    "executor": "executor_idle",
    "specialist": "specialist_idle",
    "customer": "customer_idle",
    "admin": "admin_idle",
    "blocked": "blocked_idle",
}

# Словарь состояний
STATES = {
    # Состояния гостя
    "guest_idle": "Начальное состояние гостя",
    "guest_registration_name_request": "Гость вводит имя для регистрации",
    "guest_registration_email_request": "Гость вводит email для регистрации",
    "guest_registration_role_request": "Гость выбирает роль",

    # Состояния диспетчера
    "dispatcher_idle": "Начальное состояние диспетчера",
    "dispatcher_assign_order_step_1": "Диспетчер вводит номер заказа",
    "dispatcher_assign_order_step_2": "Диспетчер выбирает исполнителя",
    "dispatcher_check_schedule": "Диспетчер проверяет расписание",
    "dispatcher_reschedule_order": "Диспетчер переносит дату заказа",  # Новое состояние

    # Состояния исполнителя
    "executor_idle": "Начальное состояние исполнителя",
    "executor_view_tasks": "Исполнитель просматривает задачи",
    "executor_complete_task": "Исполнитель завершает задачу",
    "executor_upload_photo": "Исполнитель загружает фото выполнения",
    "executor_set_date": "Исполнитель назначает дату выполнения задачи",  # Новое состояние
    "executor_add_photo": "Исполнитель добавляет фото выполнения",  # Новое состояние

    # Состояния специалиста
    "specialist_idle": "Начальное состояние специалиста",
    "specialist_view_tasks": "Специалист просматривает задачи",
    "specialist_complete_task": "Специалист завершает задачу",
    "specialist_upload_photo": "Специалист загружает фото выполнения",
    "specialist_set_date": "Специалист назначает дату монтажа",  # Новое состояние
    "specialist_add_photo": "Специалист добавляет фото выполнения",  # Новое состояние

    # Состояния заказчика
    "customer_idle": "Начальное состояние заказчика",
    "customer_create_order_step_1": "Заказчик выбирает услугу",
    "customer_create_order_step_2": "Заказчик вводит детали заказа",
    "customer_view_orders": "Заказчик просматривает заказы",

    # Состояния администратора
    "admin_idle": "Начальное состояние администратора",
    "admin_manage_users": "Администратор управляет пользователями",
    "admin_view_analytics": "Администратор просматривает аналитику",
    "admin_edit_order": "Администратор редактирует заказ",
    "admin_reply_to_user": "Администратор отвечает пользователю",  # Новое состояние
    "admin_broadcast_message": "Администратор отправляет массовое сообщение",  # Новое состояние


    # Состояния для всех
    "awaiting_admin_message": "Пользователь пишет сообщение администратору",


    # Состояния заблокированного пользователя
    "blocked_idle": "Начальное состояние заблокированного пользователя",
    "blocked_contact_admin": "Заблокированный пользователь пишет сообщение администратору",
}

