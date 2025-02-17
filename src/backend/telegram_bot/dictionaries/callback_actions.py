# src/backend/telegram_bot/dictionaries/callback_actions.py

CALLBACK_ACTIONS = {
    # Для администратора
    # Привязка префикса callback_data к обработчику
    "reply_to_": "handle_reply_button",

    # Для монтажника
    "executor_accept_order": "handle_executor_accept_order",
    "executor_decline_order": "handle_executor_decline_order",
    "executor_set_montage_date": "handle_executor_set_montage_date",  # Установить/сменить дату выполнения
    "executor_date_confirm_yes": "handle_executor_date_confirm",      # Подтвердить дату выполнения
    "executor_date_confirm_no": "handle_executor_date_confirm",       # Отменить подтверждение
    "executor_cancel_date_input": "handle_executor_cancel_date_input",  # Отмена ввода даты монтажа
    "executor_complete_order": "handle_executor_complete_order",      # Завершить заказ

    # Для специалиста
    "specialist_accept_order": "handle_specialist_accept_order",
    "specialist_decline_order": "handle_specialist_decline_order",
    "specialist_set_montage_date": "handle_specialist_set_montage_date",  # Установить/сменить дату монтажа
    "specialist_confirm_date_input": "handle_specialist_date_confirm",      # Подтвердить дату монтажа
    "specialist_cancel_date_input": "handle_specialist_cancel_date_input",  # Отмена ввода даты монтажа
    "specialist_complete_order": "handle_specialist_complete_order",      # Завершить заказ

    # Для клиента
}
