-- Таблица ролей
CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE
);

-- Таблица пользователей
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255),
    role INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role) REFERENCES roles(id)
);

-- Таблица заказов
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT,
    description TEXT,
    status ENUM('Pending', 'In Progress', 'Completed'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES users(id)
);

-- Таблица назначений
CREATE TABLE order_assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    executor_id INT,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (executor_id) REFERENCES users(id)
);
