-- Migration: Add encryption support and LMS credentials table
-- Requirements: 16.2, 12.6 - Data encryption at rest using AES-256

-- ============================================================================
-- ENABLE PGCRYPTO EXTENSION FOR DATABASE-LEVEL ENCRYPTION
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- LMS_CREDENTIALS TABLE (Encrypted credentials storage)
-- ============================================================================
CREATE TABLE lms_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    encrypted_username VARCHAR(500) NOT NULL,
    encrypted_password VARCHAR(500) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    last_used_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lms_credentials_student ON lms_credentials(student_id);
CREATE INDEX idx_lms_credentials_platform ON lms_credentials(platform);
CREATE INDEX idx_lms_credentials_is_active ON lms_credentials(is_active);

CREATE TRIGGER update_lms_credentials_updated_at BEFORE UPDATE ON lms_credentials
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE lms_credentials IS 'Stores encrypted LMS credentials for students (AES-256 encrypted at application layer)';
COMMENT ON COLUMN lms_credentials.encrypted_username IS 'AES-256 encrypted LMS username/email';
COMMENT ON COLUMN lms_credentials.encrypted_password IS 'AES-256 encrypted LMS password';

-- ============================================================================
-- REFRESH_TOKENS TABLE (Encrypted token storage)
-- ============================================================================
-- Note: refresh_tokens table already exists in schema.sql
-- Adding encryption comment for documentation
COMMENT ON TABLE refresh_tokens IS 'Stores refresh tokens (should be encrypted at application layer)';

-- ============================================================================
-- ADD ENCRYPTION METADATA TO EXISTING TABLES
-- ============================================================================
COMMENT ON COLUMN students.password_hash IS 'Bcrypt hashed password (work factor 12+)';
COMMENT ON COLUMN students.email IS 'Student email (consider encryption for PII compliance)';
COMMENT ON COLUMN students.first_name IS 'Student first name (consider encryption for PII compliance)';
COMMENT ON COLUMN students.last_name IS 'Student last name (consider encryption for PII compliance)';

-- ============================================================================
-- POSTGRESQL TRANSPARENT DATA ENCRYPTION (TDE) CONFIGURATION
-- ============================================================================
-- Note: PostgreSQL TDE requires enterprise extensions or file-system level encryption
-- For production deployment, consider:
-- 1. File-system level encryption (LUKS on Linux, BitLocker on Windows)
-- 2. PostgreSQL SSL/TLS for data in transit (already configured)
-- 3. pgcrypto for column-level encryption (enabled above)
-- 4. Application-layer encryption (implemented in EduPilot.Infrastructure.Services.EncryptionService)

-- ============================================================================
-- ENCRYPTION AUDIT LOG
-- ============================================================================
CREATE TABLE encryption_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    operation VARCHAR(20) NOT NULL, -- 'encrypt', 'decrypt', 'key_rotation'
    performed_by VARCHAR(255),
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    CONSTRAINT chk_encryption_operation CHECK (operation IN ('encrypt', 'decrypt', 'key_rotation', 'access'))
);

CREATE INDEX idx_encryption_audit_table ON encryption_audit_log(table_name);
CREATE INDEX idx_encryption_audit_performed_at ON encryption_audit_log(performed_at DESC);
CREATE INDEX idx_encryption_audit_operation ON encryption_audit_log(operation);

COMMENT ON TABLE encryption_audit_log IS 'Audit log for encryption operations (Requirements 16.2, 16.6)';

-- ============================================================================
-- ENCRYPTION HELPER FUNCTIONS (Using pgcrypto)
-- ============================================================================

-- Function to encrypt data using AES-256 (for database-level encryption if needed)
CREATE OR REPLACE FUNCTION encrypt_data(data TEXT, key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN encode(
        pgp_sym_encrypt(data, key, 'cipher-algo=aes256'),
        'base64'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to decrypt data using AES-256
CREATE OR REPLACE FUNCTION decrypt_data(encrypted_data TEXT, key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(
        decode(encrypted_data, 'base64'),
        key
    );
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL; -- Return NULL if decryption fails
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION encrypt_data IS 'Encrypts data using AES-256 via pgcrypto (for database-level encryption)';
COMMENT ON FUNCTION decrypt_data IS 'Decrypts AES-256 encrypted data via pgcrypto';

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================
GRANT ALL PRIVILEGES ON TABLE lms_credentials TO edupilot;
GRANT ALL PRIVILEGES ON TABLE encryption_audit_log TO edupilot;
GRANT EXECUTE ON FUNCTION encrypt_data TO edupilot;
GRANT EXECUTE ON FUNCTION decrypt_data TO edupilot;

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '✓ Encryption migration completed successfully!';
    RAISE NOTICE '  - pgcrypto extension enabled for AES-256 encryption';
    RAISE NOTICE '  - lms_credentials table created with encrypted fields';
    RAISE NOTICE '  - encryption_audit_log table created for compliance';
    RAISE NOTICE '  - Encryption helper functions created';
    RAISE NOTICE '';
    RAISE NOTICE 'Security Notes:';
    RAISE NOTICE '  - Application-layer encryption: EduPilot.Infrastructure.Services.EncryptionService';
    RAISE NOTICE '  - Database-level encryption: pgcrypto functions available';
    RAISE NOTICE '  - File-system encryption: Configure LUKS/BitLocker for production';
    RAISE NOTICE '  - Encryption keys: Stored in environment variables (AES_ENCRYPTION_KEY, AES_ENCRYPTION_IV)';
END $$;
