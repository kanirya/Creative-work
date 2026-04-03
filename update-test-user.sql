-- Update test user with correct BCrypt hash
-- Password: password
UPDATE students 
SET password_hash = '$2y$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi' 
WHERE email = 'test@iqra.edu.pk';
