-- Таблица roles
INSERT INTO roles (id, name) VALUES
(1, 'Administrator'),
(2, 'Dispatcher'),
(3, 'Specialist'),
(4, 'Executor'),
(5, 'Customer');

-- Таблица users
INSERT INTO users (id, name, email, password_hash, role, created_at) VALUES
(1, 'greenbandyt', 'bandurayv@yandex.ru', '$2b$12$nAPq5rto7qbIjhZiAO/lNeuDC9ywQREMD2TJbV3iZCayMdf/H/BMa', 1, '2024-11-15 05:47:11'),
(2, 'Dispatcher_1', 'dispatcher_user@example.com', '$2b$12$ENZAJUpvdmv0DIorbyvw/eeui3ISp9zbGIHI3C.HzhyeFazhYMFiW', 2, '2024-11-15 05:47:11'),
(3, 'Specialist_1', 'specialist_user@example.com', '$2b$12$47IcL8yQ7bjQgkOeObWgte.9dsnfiXilXBbX2ZiUCSUrK/bI5nlyS', 3, '2024-11-15 05:47:11'),
(4, 'Executor_1', 'executor_user@example.com', '$2b$12$SbhwbegpTer4oyNEVo6wZu8s7V8jV/RkcZs9bxT1gxmiIcnBn46fe', 4, '2024-11-15 05:47:11');

-- Таблица orders
INSERT INTO orders (id, customer_id, description, status, created_at, updated_at, assigned_at, installer_id) VALUES
(20, 1, 'Монтаж кондиционера', 'Ожидает', '2024-11-20 05:21:07', '2024-11-20 05:21:07', NULL, NULL),
(21, 1, 'Установка отопительной системы', 'Выполняется', '2024-11-20 05:21:07', '2024-11-20 05:21:07', '2024-11-20 05:21:07', 3),
(22, 1, 'Ремонт системы вентиляции', 'Завершён', '2024-11-20 05:21:07', '2024-11-20 05:21:07', '2024-11-20 05:21:07', 3);

-- Таблица customers
INSERT INTO customers (id, name, email, phone, address, created_at, password_hash) VALUES
(1, 'Customer_1', 'customer_user@example.com', NULL, NULL, '2024-11-15 05:47:11', NULL);
