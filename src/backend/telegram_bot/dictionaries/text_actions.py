# dictionaries/text_actions.py

TEXT_ACTIONS = {
    # Действия для гостя
    "✍️ Регистрация": "guest_register",
    "🆘 Помощь": "guest_help",

    # Действия для администратора
    "📊 Аналитика": "admin_analytics",
    "👥 Пользователи": "admin_users",
    "📂 Заказы": "admin_orders",
    "🔔 Уведомление": "admin_notifications",

    # Действия для диспетчера
    "📦 Текущие заказы": "dispatcher_current_orders",
    "📝 Создать заказ": "dispatcher_create_order",
    "📅 Сегодня": "dispatcher_today",

    # Действия для исполнителя
    "📋 Новые задания": "executor_new_tasks",
    "🔄 Задания в работе": "executor_in_progress",
    "📞 Написать администратору": "executor_contact_admin",

    # Действия для специалиста
    "📋 Список новых заданий": "specialist_new_tasks",
    "🔄 Текущие задания": "specialist_current_tasks",
    "📞 Связаться с администратором": "specialist_contact_admin",

    # Действия для заказчика
    "🛒 Сделать заказ": "customer_make_order",
    "📃 Мои заказы": "customer_my_orders",
    "💬 Написать": "customer_contact_admin",

    # Действия для заблокированного пользователя
    "📞 Вопрос администратору": "blocked_contact_admin",
}
