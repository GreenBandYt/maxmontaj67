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
)
from telegram_bot.bot_utils.messages.admin_user_messages import handle_user_message_to_admin


TEXT_ACTIONS = {
    # Действия для гостя
    "✍️ Регистрация": feature_in_development, #handle_guest_register,
    "🆘 Помощь": handle_guest_help,

    # Действия для администратора
    "📊 Аналитика": feature_in_development, #"admin_analytics",
    "👥 Пользователи": feature_in_development, #"admin_users",
    "📂 Заказы": feature_in_development, #"admin_orders",
    "🔔 Уведомление всем": feature_in_development, #"admin_notifications",

    # Действия для диспетчера
    "📦 Текущие заказы": feature_in_development, #"dispatcher_current_orders",
    "📝 Создать заказ": feature_in_development, #"dispatcher_create_order",
    "📅 Сегодня": feature_in_development, #"dispatcher_today",
    # "📞 Написать администратору"

    # Действия для специалиста
    "📋 Список новых заданий": handle_specialist_new_tasks,  # Список новых заданий
    "🔄 Текущие задания": handle_specialist_current_tasks,  # Текущие задания
    # "📞 Написать администратору"

    # Дополнительные меню для специалиста
    "📅 Дата монтажа": feature_in_development, #handle_specialist_montage_menu,  # Меню для управления датой монтажа
    "✅ Завершение заказа": feature_in_development, #handle_specialist_complete_menu,  # Меню для завершения заказа

    # Действия для исполнителя
    "📋 Новые задания": handle_executor_new_tasks,  # Список новых заданий
    "🔄 Задания в работе": handle_executor_current_tasks,  # Текущие задания
    # "📞 Написать администратору"

    # Дополнительные меню для исполнителя
    "📅 Дата выполнения": handle_executor_montage_menu,  # Меню для управления датой монтажа
    "✅ Закрытие заказа": handle_executor_complete_menu,  # Меню для завершения заказа

    # Действия для заказчика
    "🛒 Сделать заказ": feature_in_development,  # Сделать заказ
    "📃 Мои заказы": feature_in_development,  # Мои заказы
    # "📞 Написать администратору"

    # Действия для заблокированного пользователя


    # Действия для всех
    "📞 Написать администратору": handle_user_message_to_admin,  # Привязываем реальный обработчик

}

