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


# Словарь обработчиков состояний
STATE_HANDLERS = {

    # Общие состояния
    "writing_message": "process_admin_message",
    "replying_to_user": "handle_reply_message",

    # # Для гостей
    "registration_name": "handle_guest_registration_name_request",
    # "guest_registration_email_request": handle_guest_registration_email_request,
    # "guest_registration_role_request": handle_guest_registration_role_request,

    # # Для диспетчеров
    # "dispatcher_assign_order_step_1": handle_dispatcher_assign_order_step_1,
    # "dispatcher_assign_order_step_2": handle_dispatcher_assign_order_step_2,
    # "dispatcher_check_schedule": handle_dispatcher_check_schedule,

    # # Для исполнителей

    "executor_view_tasks": "handle_executor_view_tasks",
    "executor_complete_task": "handle_executor_complete_task",
    "executor_upload_photo": "handle_executor_upload_photo",
    "executor_date_input": "handle_executor_date_input",
    "executor_date_confirm": "handle_executor_date_confirm",
    "executor_cancel_date_input": "handle_executor_cancel_date_input",

    # Для специалистов
    "specialist_view_tasks": "handle_specialist_view_tasks",
    "specialist_complete_task": "handle_specialist_complete_task",
    "specialist_upload_photo": "handle_specialist_upload_photo",
    "specialist_date_input": "handle_specialist_date_input",
    "specialist_date_confirm": "handle_specialist_date_confirm",
    "specialist_cancel_date_input": "handle_specialist_cancel_date_input",

    # # Для заказчиков
    # "customer_create_order_step_1": handle_customer_create_order_step_1,
    # "customer_create_order_step_2": handle_customer_create_order_step_2,
    # "customer_view_orders": handle_customer_view_orders,

    # Для администраторов
    "admin_manage_users": "handle_admin_manage_users",
    "admin_view_analytics": "handle_admin_view_analytics",
    "admin_edit_order": "handle_admin_edit_order",

    # # Для заблокированных пользователей
    # "blocked_contact_admin": handle_blocked_contact_admin,
}
# Словарь состояний (заготовка)
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

    # Состояния исполнителя
    "executor_idle": "Начальное состояние исполнителя",
    "executor_view_tasks": "Исполнитель просматривает задачи",
    "executor_complete_task": "Исполнитель завершает задачу",
    "executor_upload_photo": "Исполнитель загружает фото выполнения",

    # Состояния специалиста
    "specialist_idle": "Начальное состояние специалиста",
    "specialist_view_tasks": "Специалист просматривает задачи",
    "specialist_complete_task": "Специалист завершает задачу",
    "specialist_upload_photo": "Специалист загружает фото выполнения",


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

    # Состояния заблокированного пользователя
    "blocked_idle": "Начальное состояние заблокированного пользователя",
    "blocked_contact_admin": "Заблокированный пользователь пишет сообщение администратору",
}

