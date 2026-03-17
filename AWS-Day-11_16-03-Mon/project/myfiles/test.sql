USE test;

-- Check table was created by Flask
SHOW TABLES;

-- Insert sample records
INSERT INTO users (name, email) VALUES
('Fardeena Attar',  'fardeen@example.com'),
('John Smith',      'john.smith@example.com'),
('Priya Sharma',    'priya.sharma@example.com'),
('Mohammed Ali',    'mohammed.ali@example.com'),
('Sarah Johnson',   'sarah.johnson@example.com');

-- Verify records
SELECT * FROM users;
