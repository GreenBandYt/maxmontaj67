-- Таблица ролей
CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE,
    UNIQUE KEY name (name)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- Таблица пользователей
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255),
    role INT,
    created_at TIMESTAMP NULL DEFAULT current_timestamp(),
    UNIQUE KEY email (email),
    KEY role (role),
    FOREIGN KEY (role) REFERENCES roles(id)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Таблица заказов
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    description TEXT,
    status ENUM('Ожидает', 'Выполняется', 'Завершён') NOT NULL,
    created_at TIMESTAMP NULL DEFAULT current_timestamp(),
    updated_at TIMESTAMP NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    assigned_at TIMESTAMP NULL DEFAULT NULL,
    installer_id INT,
    KEY fk_orders_customer (customer_id),
    KEY fk_orders_installer (installer_id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (installer_id) REFERENCES users(id)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- Таблица клиентов
CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20) DEFAULT NULL,
    address TEXT DEFAULT NULL,
    created_at TIMESTAMP NULL DEFAULT current_timestamp(),
    password_hash VARCHAR(255) DEFAULT NULL
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
