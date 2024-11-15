-- Создание таблиц и наполнение данными

-- Таблица roles
INSERT INTO roles (id, name) VALUES
(1, 'Administrator'),
(2, 'Dispatcher'),
(3, 'Specialist'),
(4, 'Executor'),
(5, 'Customer');

-- Таблица users
INSERT INTO users (id, name, email, password_hash, role, created_at) VALUES
(1, 'greenbandyt', 'bandurayv@yandex.ru', MD5('byv5054byv'), 1, '2024-11-10 00:00:00'),
(2, 'Dispatcher_1', 'dispatcher_user@example.com', MD5('Dispatcher_1'), 2, '2024-11-10 00:00:00'),
(3, 'Specialist_1', 'specialist_user@example.com', MD5('Specialist_1'), 3, '2024-11-10 00:00:00'),
(4, 'Executor_1', 'executor_user@example.com', MD5('Executor_1'), 4, '2024-11-10 00:00:00'),
(5, 'Customer_1', 'customer_user@example.com', MD5('Customer_1'), 5, '2024-11-10 00:00:00');

-- Таблица orders
INSERT INTO orders (id, client_id, description, status, created_at, updated_at) VALUES
(1, 5, 'Install new equipment.', 'Pending', '2024-11-11 10:00:00', '2024-11-11 10:00:00'),
(2, 5, 'Repair old equipment.', 'In Progress', '2024-11-12 14:00:00', '2024-11-12 15:00:00'),
(3, 5, 'Perform annual maintenance.', 'Completed', '2024-11-10 09:00:00', '2024-11-10 12:00:00');

-- Таблица order_assignments
INSERT INTO order_assignments (id, order_id, executor_id, assigned_at) VALUES
(1, 1, 4, '2024-11-11 11:00:00'),
(2, 2, 4, '2024-11-12 14:30:00'),
(3, 3, 4, '2024-11-10 09:30:00');
