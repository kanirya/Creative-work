# Data Encryption at Rest Implementation

**Task:** 21.2 - Implement data encryption at rest  
**Requirements:** 16.2, 12.6  
**Encryption Standard:** AES-256

## Overview

This document describes the implementation of data encryption at rest for the EduPilot system, ensuring sensitive student data is protected using industry-standard AES-256 encryption.

## Architecture

The encryption implementation uses a **multi-layered approach**:

### 1. Application-Layer Encryption (Primary)
- **Service:** `EduPilot.Infrastructure.Services.EncryptionService`
- **Algorithm:** AES-256-CBC
- **Key Management:** Environment variables (`AES_ENCRYPTION_KEY`, `AES_ENCRYPTION_IV`)
- **Use Cases:**
  - LMS credentials (username, password)
  - Refresh tokens
  - Personal identifiable information (PII)
  - Any sensitive data requiring encryption

### 2. Database-Layer Encryption (Secondary)
- **Extension:** pgcrypto
- **Functions:** `encrypt_data()`, `decrypt_data()`
- **Use Cases:**
  - Column-level encryption for highly sensitive data
  - Database-level encryption operations
  - Backup encryption

### 3. File-System Encryption (Infrastructure)
- **Production Recommendation:** LUKS (Linux) or BitLocker (Windows)
- **Cloud Options:** AWS EBS encryption, Azure Disk Encryption, GCP persistent disk encryption
- **Benefit:** Transparent encryption of entire database files

## Implementation Details

### Application-Layer Encryption

#### EncryptionService

```csharp
public interface IEncryptionService
{
    string Encrypt(string plainText);
    string Decrypt(string cipherText);
    byte[] EncryptBytes(byte[] plainBytes);
    byte[] DecryptBytes(byte[] cipherBytes);
}
```

**Features:**
- AES-256 encryption with CBC mode
- PKCS7 padding
- Base64 encoding for string storage
- Automatic key derivation using SHA-256
- Thread-safe implementation

#### Encrypted Entities

**LmsCredential Entity:**
```csharp
public class LmsCredential : BaseEntity
{
    public string EncryptedUsername { get; private set; }
    public string EncryptedPassword { get; private set; }
    public string Platform { get; private set; }
    // ...
}
```

**Usage Example:**
```csharp
// Encrypting credentials
var encryptionService = serviceProvider.GetRequiredService<IEncryptionService>();
var encryptedUsername = encryptionService.Encrypt(plainUsername);
var encryptedPassword = encryptionService.Encrypt(plainPassword);

var credential = LmsCredential.Create(
    studentId,
    encryptedUsername,
    encryptedPassword,
    "IqraUniversity"
);

// Decrypting credentials
var plainUsername = encryptionService.Decrypt(credential.EncryptedUsername);
var plainPassword = encryptionService.Decrypt(credential.EncryptedPassword);
```

### Database Schema

#### LMS Credentials Table
```sql
CREATE TABLE lms_credentials (
    id UUID PRIMARY KEY,
    student_id UUID NOT NULL,
    encrypted_username VARCHAR(500) NOT NULL,
    encrypted_password VARCHAR(500) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    last_used_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Encryption Audit Log
```sql
CREATE TABLE encryption_audit_log (
    id UUID PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    operation VARCHAR(20) NOT NULL,
    performed_by VARCHAR(255),
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL,
    error_message TEXT
);
```

### PostgreSQL Configuration

#### Encryption Extensions
```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

#### Helper Functions
```sql
-- Encrypt data using AES-256
CREATE FUNCTION encrypt_data(data TEXT, key TEXT) RETURNS TEXT;

-- Decrypt data using AES-256
CREATE FUNCTION decrypt_data(encrypted_data TEXT, key TEXT) RETURNS TEXT;
```

## Configuration

### Environment Variables

Add to `.env` file:
```bash
# AES Encryption - 32 bytes key and 16 bytes IV
AES_ENCRYPTION_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
AES_ENCRYPTION_IV=1a2b3c4d5e6f7g8h
```

**Important:** 
- Generate secure random keys for production
- Never commit encryption keys to version control
- Use different keys for different environments
- Store keys in secure key management system (AWS KMS, Azure Key Vault, HashiCorp Vault)

### Generating Secure Keys

```bash
# Generate 32-byte key (256 bits)
openssl rand -base64 32

# Generate 16-byte IV (128 bits)
openssl rand -base64 16
```

## Security Best Practices

### Key Management

1. **Key Storage:**
   - Development: Environment variables
   - Production: Key management service (AWS KMS, Azure Key Vault, HashiCorp Vault)
   - Never hardcode keys in source code

2. **Key Rotation:**
   - Rotate encryption keys every 90 days
   - Implement dual-key encryption for zero-downtime rotation
   - Keep old keys for decrypting historical data

3. **Key Access Control:**
   - Limit key access to authorized services only
   - Use IAM roles and policies
   - Audit key access regularly

### Data Protection

1. **Encrypt Sensitive Fields:**
   - Passwords (use bcrypt for hashing, not encryption)
   - LMS credentials
   - Refresh tokens
   - Personal identifiable information (PII)
   - Financial information

2. **Don't Encrypt Everything:**
   - Non-sensitive data (course names, public announcements)
   - Indexed fields (impacts query performance)
   - Frequently accessed data (consider caching)

3. **Encryption in Transit:**
   - Use TLS 1.3 for all network communication
   - Configure PostgreSQL SSL/TLS
   - Verify certificate validation

### Compliance

1. **FERPA Compliance:**
   - Encrypt student records
   - Implement access logging (encryption_audit_log)
   - Regular security audits

2. **Audit Trail:**
   - Log all encryption/decryption operations
   - Monitor encryption_audit_log for suspicious activity
   - Retain logs for compliance period (typically 7 years)

## Performance Considerations

### Overhead

- **Application-layer encryption:** ~5-10% CPU overhead
- **File-system encryption:** ~2-5% I/O overhead
- **Column-level encryption:** ~10-20% query overhead

### Optimization

1. **Hardware Acceleration:**
   - Use CPUs with AES-NI instruction set
   - Enable hardware acceleration in OpenSSL

2. **Caching:**
   - Cache decrypted data in application layer
   - Set appropriate TTL for cached data
   - Invalidate cache on data updates

3. **Selective Encryption:**
   - Encrypt only sensitive fields
   - Avoid encrypting indexed columns
   - Use application-layer encryption for better performance

4. **Connection Pooling:**
   - Reduce SSL handshake overhead
   - Configure appropriate pool size

## Testing

### Unit Tests

Test encryption service:
```csharp
[Fact]
public void Encrypt_Decrypt_RoundTrip_ShouldReturnOriginalText()
{
    // Arrange
    var service = new EncryptionService(configuration);
    var plainText = "sensitive data";
    
    // Act
    var encrypted = service.Encrypt(plainText);
    var decrypted = service.Decrypt(encrypted);
    
    // Assert
    Assert.Equal(plainText, decrypted);
    Assert.NotEqual(plainText, encrypted);
}
```

### Integration Tests

Test encrypted entity storage:
```csharp
[Fact]
public async Task LmsCredential_ShouldStoreAndRetrieveEncrypted()
{
    // Arrange
    var credential = LmsCredential.Create(
        studentId,
        encryptedUsername,
        encryptedPassword,
        "IqraUniversity"
    );
    
    // Act
    await dbContext.LmsCredentials.AddAsync(credential);
    await dbContext.SaveChangesAsync();
    
    var retrieved = await dbContext.LmsCredentials
        .FirstOrDefaultAsync(c => c.StudentId == studentId);
    
    // Assert
    Assert.NotNull(retrieved);
    Assert.Equal(encryptedUsername, retrieved.EncryptedUsername);
}
```

## Deployment

### Development

1. Run database migrations:
```bash
docker-compose down -v
docker-compose up -d postgres
```

2. Verify encryption extension:
```sql
SELECT * FROM pg_extension WHERE extname = 'pgcrypto';
```

3. Test encryption functions:
```sql
SELECT encrypt_data('test data', 'test_key');
```

### Production

1. **File-System Encryption:**
```bash
# Linux (LUKS)
cryptsetup luksFormat /dev/sdb
cryptsetup luksOpen /dev/sdb encrypted_disk
mkfs.ext4 /dev/mapper/encrypted_disk
mount /dev/mapper/encrypted_disk /var/lib/postgresql/data
```

2. **PostgreSQL SSL:**
```bash
# Generate SSL certificates
openssl req -new -x509 -days 365 -nodes -text \
  -out server.crt -keyout server.key -subj "/CN=postgres"
chmod 600 server.key
chown postgres:postgres server.key server.crt
```

3. **Configure PostgreSQL:**
```bash
# Add to postgresql.conf
ssl = on
ssl_cert_file = '/var/lib/postgresql/server.crt'
ssl_key_file = '/var/lib/postgresql/server.key'
password_encryption = scram-sha-256
```

4. **Verify Encryption:**
```bash
# Check SSL connection
psql "postgresql://user@host/db?sslmode=require"

# Verify data checksums
psql -c "SHOW data_checksums;"
```

## Monitoring

### Metrics to Track

1. **Encryption Operations:**
   - Encryption/decryption success rate
   - Operation latency
   - Error rate

2. **Key Usage:**
   - Key access frequency
   - Failed decryption attempts
   - Key rotation events

3. **Performance:**
   - Query performance with encrypted fields
   - CPU usage for encryption operations
   - Cache hit rate for decrypted data

### Alerts

Set up alerts for:
- Failed decryption attempts (potential key issues)
- High encryption error rate
- Unusual access patterns to encrypted data
- Key rotation failures

## Troubleshooting

### Common Issues

1. **Decryption Fails:**
   - Verify encryption key matches
   - Check key format (base64, hex)
   - Ensure IV is correct

2. **Performance Degradation:**
   - Check if too many fields are encrypted
   - Verify hardware acceleration is enabled
   - Review caching strategy

3. **Key Rotation Issues:**
   - Implement dual-key decryption
   - Keep old keys for historical data
   - Test rotation in staging first

## References

- [NIST AES Specification](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.197.pdf)
- [PostgreSQL pgcrypto Documentation](https://www.postgresql.org/docs/current/pgcrypto.html)
- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- [FERPA Compliance Guidelines](https://www2.ed.gov/policy/gen/guid/fpco/ferpa/index.html)

## Conclusion

The encryption implementation provides comprehensive protection for sensitive data at rest using AES-256 encryption. The multi-layered approach ensures defense in depth, with application-layer encryption for sensitive fields, database-level encryption capabilities, and recommendations for file-system encryption in production.

**Key Takeaways:**
- ✅ AES-256 encryption implemented for sensitive data
- ✅ Application-layer encryption service created
- ✅ Database schema updated with encrypted fields
- ✅ PostgreSQL pgcrypto extension enabled
- ✅ Encryption audit logging implemented
- ✅ Security best practices documented
- ✅ Performance optimization guidelines provided
