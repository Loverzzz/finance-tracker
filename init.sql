-- Script to initialize the PostgreSQL database schema for the Financial Tracker

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE account_settings (
    user_id INT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    total_gaji DECIMAL(15, 2) DEFAULT 0.00,
    target_menabung_persen DECIMAL(5, 2) DEFAULT 0.00
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    tanggal_input TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tanggal_struk DATE NOT NULL,
    toko VARCHAR(255) NOT NULL,
    total_item INT DEFAULT 1,
    items_array JSONB,
    category VARCHAR(100) NOT NULL,
    method VARCHAR(100) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    mood VARCHAR(50),
    image_path VARCHAR(255),
    tipe_kirim VARCHAR(50)
);

CREATE TABLE budgets (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    month INT NOT NULL,
    year INT NOT NULL,
    needs_target_amount DECIMAL(15, 2) DEFAULT 0.00,
    wants_target_amount DECIMAL(15, 2) DEFAULT 0.00,
    savings_target_amount DECIMAL(15, 2) DEFAULT 0.00,
    UNIQUE (user_id, month, year)
);
