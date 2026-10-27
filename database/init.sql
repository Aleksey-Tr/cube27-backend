CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL -- Название роли
);
-- Роли пользователей

CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL, -- Название компании
    inn VARCHAR(12) UNIQUE NOT NULL, -- ИНН компании для бухгалтерии и договоров
    address TEXT, -- Юридический адрес компании
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Дата регистрации компании в системе
);
-- Общая информация о компании арендodatorой

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    company_id INT REFERENCES companies (id) ON DELETE CASCADE,
    role_id INT REFERENCES roles (id) NOT NULL, -- Ссылка на роль пользователя
    first_name VARCHAR(100) NOT NULL, -- Имя
    last_name VARCHAR(100) NOT NULL, -- Фамилия
    email VARCHAR(255) UNIQUE NOT NULL, -- Email
    phone VARCHAR(20), -- Номер телефона
    password_hash VARCHAR(255) NOT NULL, -- Захешированный пароль
    is_active BOOLEAN DEFAULT FALSE -- Флаг доступности пользователя к лк
);
-- Пользователь и личный кабинет

CREATE TABLE premises (
    id SERIAL PRIMARY KEY,
    floor INT NOT NULL, -- Этаж, на котором находится помещение
    room_number VARCHAR(50) NOT NULL, -- Номер помещения
    area DECIMAL(10, 2) NOT NULL, -- Площадь в квадратных метрах
    status VARCHAR(50) DEFAULT 'Free', -- Статус доступности помещения
    price DECIMAL(12, 2) NOT NULL -- Базовая стоимость аренды в месяц
);
-- Помещение и общая информация

CREATE TABLE contracts (
    id SERIAL PRIMARY KEY,
    company_id INT REFERENCES companies (id) ON DELETE CASCADE,
    contract_number VARCHAR(100) UNIQUE NOT NULL, -- Юридический номер договора
    start_date DATE NOT NULL, -- Дата начала договора
    end_date DATE NOT NULL, -- Дата окончания договора
    status VARCHAR(50) DEFAULT 'Active' -- Статус договора
);
-- Договор аренды

CREATE TABLE contract_premises (
    contract_id INT REFERENCES contracts (id) ON DELETE CASCADE,
    premise_id INT REFERENCES premises (id) ON DELETE CASCADE,
    PRIMARY KEY (contract_id, premise_id)
);
-- Связь между договорами и помещениями в том случае если договор предусматривает несколько помещений

CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    contract_id INT REFERENCES contracts (id) ON DELETE CASCADE,
    amount DECIMAL(12, 2) NOT NULL, -- Сумма к оплате
    status VARCHAR(50) DEFAULT 'Unpaid', -- Статус
    due_date DATE NOT NULL, -- Крайний срок оплаты
    issued_date DATE NOT NULL -- Дата выставления счета бухгалтером
);
-- Финансовые счета на оплату аренды

CREATE TABLE meters (
    id SERIAL PRIMARY KEY,
    premise_id INT REFERENCES premises (id) ON DELETE CASCADE,
    meter_type VARCHAR(50) NOT NULL, -- Тип счетчика
    serial_number VARCHAR(100) UNIQUE NOT NULL -- Номер прибора
);
-- Общая информация о счетчиках

CREATE TABLE meter_readings (
    id SERIAL PRIMARY KEY,
    meter_id INT REFERENCES meters (id) ON DELETE CASCADE,
    user_id INT REFERENCES users (id) ON DELETE SET NULL,
    value DECIMAL(12, 2) NOT NULL, -- Значение счетчика
    reading_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Дата отправки показаний
    status VARCHAR(50) DEFAULT 'Pending' -- Статус проверки
);
-- Показания счетчиков

CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    author_id INT REFERENCES users (id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL, -- Категория обращения
    subject VARCHAR(255) NOT NULL, -- Тема заявки
    description TEXT NOT NULL, -- Текст описания проблемы
    status VARCHAR(50) DEFAULT 'Open', -- Статус заявки
    bitrix_task_id VARCHAR(100), -- ID созданной задачи в Битрикс24
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Дата и время создания заявки
);
-- Заявки на обслуживание