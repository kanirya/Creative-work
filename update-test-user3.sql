-- Update test user with BCrypt hash for "test123"
UPDATE students 
SET password_hash = '$2y$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEg7dO' 
WHERE email = 'test@iqra.edu.pk';
