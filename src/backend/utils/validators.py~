def is_user_data_complete(user_data):
    """
    Проверяет, заполнены ли все обязательные поля пользователя.

    Аргументы:
        user_data (dict): Словарь с данными пользователя.

    Возвращает:
        bool: True, если все обязательные поля заполнены, иначе False.
    """
    required_fields = ['phone', 'address', 'passport_data', 'passport_issued_by', 'passport_issue_date']
    # Проверяем, что все поля заполнены (не None и не пустая строка)
    return all(user_data.get(field) for field in required_fields)
