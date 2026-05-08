-- 1. Setup Timezone for the Philippines
ALTER DATABASE surveillance_db SET timezone TO 'Asia/Manila';

-- 2. Wipe old tables to avoid conflicts
DROP TABLE IF EXISTS login_logs CASCADE;
DROP TABLE IF EXISTS camera_logs CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 3. Create the updated Users Table with Role
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role VARCHAR(20) DEFAULT 'user'
);

-- 4. Create Camera Logs Table
CREATE TABLE camera_logs (
    id SERIAL PRIMARY KEY,
    camera_name VARCHAR(100),
    status VARCHAR(20),
    log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Create Login Logs Table
CREATE TABLE login_logs (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Insert your accounts
-- This sets you as the 'developer' so you can see the special UI later
INSERT INTO users (username, password, role) 
VALUES ('yvan', 'admin123', 'developer');

-- Standard user for testing
INSERT INTO users (username, password, role) 
VALUES ('guest', 'password123', 'user');

-- 7. Add sample camera data
INSERT INTO camera_logs (camera_name, status)
VALUES 
('Front Gate Camera', 'ONLINE'),
('Parking Camera', 'OFFLINE');