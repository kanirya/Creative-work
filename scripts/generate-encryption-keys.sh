#!/bin/bash

# Script to generate secure encryption keys for EduPilot
# Requirements: 16.2, 12.6 - AES-256 encryption keys

set -e

echo "=========================================="
echo "EduPilot Encryption Key Generator"
echo "=========================================="
echo ""
echo "This script generates secure random keys for AES-256 encryption."
echo "IMPORTANT: Store these keys securely and never commit them to version control!"
echo ""

# Check if openssl is installed
if ! command -v openssl &> /dev/null; then
    echo "Error: openssl is not installed. Please install it first."
    exit 1
fi

# Generate 32-byte (256-bit) encryption key
echo "Generating AES-256 encryption key (32 bytes)..."
AES_KEY=$(openssl rand -base64 32 | tr -d '\n')
echo "AES_ENCRYPTION_KEY=$AES_KEY"
echo ""

# Generate 16-byte (128-bit) initialization vector
echo "Generating AES initialization vector (16 bytes)..."
AES_IV=$(openssl rand -base64 16 | tr -d '\n')
echo "AES_ENCRYPTION_IV=$AES_IV"
echo ""

# Generate JWT secret key (32 bytes)
echo "Generating JWT secret key (32 bytes)..."
JWT_KEY=$(openssl rand -hex 32 | tr -d '\n')
echo "JWT_SECRET_KEY=$JWT_KEY"
echo ""

echo "=========================================="
echo "Keys generated successfully!"
echo "=========================================="
echo ""
echo "Add these to your .env file:"
echo ""
echo "# AES Encryption Keys"
echo "AES_ENCRYPTION_KEY=$AES_KEY"
echo "AES_ENCRYPTION_IV=$AES_IV"
echo ""
echo "# JWT Secret Key"
echo "JWT_SECRET_KEY=$JWT_KEY"
echo ""
echo "=========================================="
echo "Security Recommendations:"
echo "=========================================="
echo "1. Store keys in a secure key management service (AWS KMS, Azure Key Vault, HashiCorp Vault)"
echo "2. Use different keys for different environments (dev, staging, production)"
echo "3. Rotate keys every 90 days"
echo "4. Never commit keys to version control"
echo "5. Restrict access to keys using IAM policies"
echo "6. Enable audit logging for key access"
echo "7. Backup keys securely in case of emergency"
echo ""
echo "For production deployment:"
echo "- Use environment variables or secrets management"
echo "- Enable file-system encryption (LUKS on Linux, BitLocker on Windows)"
echo "- Configure PostgreSQL SSL/TLS"
echo "- Implement key rotation strategy"
echo ""
