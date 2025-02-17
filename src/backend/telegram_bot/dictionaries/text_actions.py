# dictionaries/text_actions.py
from telegram_bot.handlers.guest.guest_menu import handle_guest_register, handle_guest_help
from telegram_bot.handlers.common_helpers import feature_in_development
from telegram_bot.handlers.executor.executor_menu import (
    handle_executor_new_tasks,
    handle_executor_current_tasks,
    handle_executor_montage_menu,
    handle_executor_complete_menu,
)
from telegram_bot.handlers.specialist.specialist_menu import (
    handle_specialist_new_tasks,
    handle_specialist_current_tasks,
    handle_specialist_montage_menu,
    handle_specialist_complete_menu,
    handle_specialist_date_input,
    handle_specialist_cancel_date_input,
    handle_specialist_return_to_menu

)
from telegram_bot.bot_utils.admin_messaging import handle_message_to_admin


TEXT_ACTIONS = {
    # Действия для гостя
    "✍️ Регистрация": feature_in_development,  # handle_guest_register,
    "🆘 Помощь": handle_guest_help,

    # Действия для администратора
    "📊 Аналитика": feature_in_development,  # "admin_analytics",
    "👥 Пользователи": feature_in_development,  # "admin_users",
    "📂 Заказы": feature_in_development,  # "admin_orders",
    "🔔 Уведомление всем": feature_in_development,  # "admin_notifications",

    # Действия для диспетчера
    "📦 Текущие заказы": feature_in_development,  # "dispatcher_current_orders",
    "📝 Создать заказ": feature_in_development,  # "dispatcher_create_order",
    "📅 Сегодня": feature_in_development,  # "dispatcher_today",

    # Действия для специалиста
    "📋 Список новых заданий": handle_specialist_new_tasks,  # Список новых заданий
    "🔄 Текущие задания": handle_specialist_current_tasks,  # Текущие задания
    "⬅️ В МЕНЮ": handle_specialist_new_tasks,  # Возврат в список текущих заказов

    # Дополнительные меню для специалиста


    # Действия для исполнителя
    "📋 Новые задания": handle_executor_new_tasks,  # Список новых заданий
    "🔄 Задания в работе": handle_executor_current_tasks,  # Текущие задания
    "⬅️ Возврат в меню": handle_specialist_return_to_menu,  # Возврат в список текущих заказов

    # Дополнительные меню для исполнителя


    # Действия для заказчика
    "🛒 Сделать заказ": feature_in_development,  # Сделать заказ
    "📃 Мои заказы": feature_in_development,  # Мои заказы

    # Действия для всех
    "📞 Написать администратору": handle_message_to_admin,  # Привязываем обработчик
}
