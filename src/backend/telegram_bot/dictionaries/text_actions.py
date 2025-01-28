# dictionaries/text_actions.py
from telegram_bot.handlers.guest.guest_menu import handle_guest_register, handle_guest_help
from telegram_bot.handlers.common_helpers import feature_in_development

TEXT_ACTIONS = {
    # Действия для гостя
    "✍️ Регистрация": feature_in_development, #handle_guest_register,
    "🆘 Помощь": handle_guest_help,

    # Действия для администратора
    "📊 Аналитика": feature_in_development, #"admin_analytics",
    "👥 Пользователи": feature_in_development, #"admin_users",
    "📂 Заказы": feature_in_development, #"admin_orders",
    "🔔 Уведомление": feature_in_development, #"admin_notifications",

    # Действия для диспетчера
    "📦 Текущие заказы": feature_in_development, #"dispatcher_current_orders",
    "📝 Создать заказ": feature_in_development, #"dispatcher_create_order",
    "📅 Сегодня": feature_in_development, #"dispatcher_today",

    # Действия для исполнителя
    "📋 Новые задания": feature_in_development, #"executor_new_tasks",
    "🔄 Задания в работе": feature_in_development, #"executor_in_progress",
    "📞 Написать администратору": feature_in_development, #"executor_contact_admin",

    # Действия для специалиста
    "📋 Список новых заданий": feature_in_development, #"specialist_new_tasks",
    "🔄 Текущие задания": feature_in_development, #"specialist_current_tasks",
    "📞 Связаться с администратором": feature_in_development, #"specialist_contact_admin",

    # Действия для заказчика
    "🛒 Сделать заказ": feature_in_development, #"customer_make_order",
    "📃 Мои заказы": feature_in_development, #"customer_my_orders",
    "💬 Написать": feature_in_development, #"customer_contact_admin",

    # Действия для заблокированного пользователя
    "📞 Вопрос администратору": feature_in_development, #"blocked_contact_admin",
}
