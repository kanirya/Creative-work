-- Update test user with BCrypt hash for "test"
-- Generated using BCrypt.Net-Next 4.0.2 with workFactor 12
UPDATE students 
SET password_hash = '$2y$12$K2nh/g2.yHJwLqKoUeH8ZOxH7VqKp3nJ5vXxH7VqKp3nJ5vXxH7Vq' 
WHERE email = 'test@iqra.edu.pk';
