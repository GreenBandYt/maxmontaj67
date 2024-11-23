from utils.validators import is_user_data_complete

# Тестовые данные
def test_is_user_data_complete():
    # Полные данные
    user_data_complete = {
        'phone': '+1234567890',
        'address': '123 Main Street',
        'passport_data': 'EncryptedPassportData',
        'passport_issued_by': 'Some Authority',
        'passport_issue_date': '2024-01-01'
    }
    assert is_user_data_complete(user_data_complete) == True, "Полные данные должны быть валидными"

    # Неполные данные (пустой адрес)
    user_data_incomplete = {
        'phone': '+1234567890',
        'address': '',
        'passport_data': 'EncryptedPassportData',
        'passport_issued_by': 'Some Authority',
        'passport_issue_date': '2024-01-01'
    }
    assert is_user_data_complete(user_data_incomplete) == False, "Неполные данные не должны быть валидными"

    print("Все тесты пройдены!")

# Запуск тестов
if __name__ == "__main__":
    test_is_user_data_complete()

