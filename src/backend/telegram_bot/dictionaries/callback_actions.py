# src/backend/telegram_bot/dictionaries/callback_actions.py

# Пример callback_data и связанных функций
CALLBACK_ACTIONS = {
    # Для администратора

    # Для диспетчера

    # Для монтажника
    "executor_accept_order": "handle_executor_accept_order",
    "executor_decline_order": "handle_executor_decline_order",

    # Для специалиста
    "specialist_accept_order": "handle_specialist_accept_order",
    "specialist_decline_order": "handle_specialist_decline_order",

    # Для клиента
}
