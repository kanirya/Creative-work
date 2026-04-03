# PowerShell script to generate secure encryption keys for EduPilot
# Requirements: 16.2, 12.6 - AES-256 encryption keys

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "EduPilot Encryption Key Generator" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script generates secure random keys for AES-256 encryption." -ForegroundColor Yellow
Write-Host "IMPORTANT: Store these keys securely and never commit them to version control!" -ForegroundColor Red
Write-Host ""

# Function to generate random bytes and convert to base64
function Generate-RandomBase64 {
    param (
        [int]$ByteCount
    )
    $bytes = New-Object byte[] $ByteCount
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    return [Convert]::ToBase64String($bytes)
}

# Function to generate random hex string
function Generate-RandomHex {
    param (
        [int]$ByteCount
    )
    $bytes = New-Object byte[] $ByteCount
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    return ($bytes | ForEach-Object { $_.ToString("x2") }) -join ''
}

try {
    # Generate 32-byte (256-bit) encryption key
    Write-Host "Generating AES-256 encryption key (32 bytes)..." -ForegroundColor Green
    $AES_KEY = Generate-RandomBase64 -ByteCount 32
    Write-Host "AES_ENCRYPTION_KEY=$AES_KEY" -ForegroundColor White
    Write-Host ""

    # Generate 16-byte (128-bit) initialization vector
    Write-Host "Generating AES initialization vector (16 bytes)..." -ForegroundColor Green
    $AES_IV = Generate-RandomBase64 -ByteCount 16
    Write-Host "AES_ENCRYPTION_IV=$AES_IV" -ForegroundColor White
    Write-Host ""

    # Generate JWT secret key (32 bytes)
    Write-Host "Generating JWT secret key (32 bytes)..." -ForegroundColor Green
    $JWT_KEY = Generate-RandomHex -ByteCount 32
    Write-Host "JWT_SECRET_KEY=$JWT_KEY" -ForegroundColor White
    Write-Host ""

    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Keys generated successfully!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Add these to your .env file:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "# AES Encryption Keys" -ForegroundColor Gray
    Write-Host "AES_ENCRYPTION_KEY=$AES_KEY" -ForegroundColor White
    Write-Host "AES_ENCRYPTION_IV=$AES_IV" -ForegroundColor White
    Write-Host ""
    Write-Host "# JWT Secret Key" -ForegroundColor Gray
    Write-Host "JWT_SECRET_KEY=$JWT_KEY" -ForegroundColor White
    Write-Host ""

    # Optionally save to file
    $saveToFile = Read-Host "Do you want to save these keys to a file? (y/n)"
    if ($saveToFile -eq 'y' -or $saveToFile -eq 'Y') {
        $filename = "encryption-keys-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
        $content = @"
# EduPilot Encryption Keys
# Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
# IMPORTANT: Store securely and never commit to version control!

# AES Encryption Keys
AES_ENCRYPTION_KEY=$AES_KEY
AES_ENCRYPTION_IV=$AES_IV

# JWT Secret Key
JWT_SECRET_KEY=$JWT_KEY
"@
        $content | Out-File -FilePath $filename -Encoding UTF8
        Write-Host ""
        Write-Host "Keys saved to: $filename" -ForegroundColor Green
        Write-Host "IMPORTANT: Delete this file after securely storing the keys!" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Security Recommendations:" -ForegroundColor Yellow
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "1. Store keys in a secure key management service (AWS KMS, Azure Key Vault, HashiCorp Vault)"
    Write-Host "2. Use different keys for different environments (dev, staging, production)"
    Write-Host "3. Rotate keys every 90 days"
    Write-Host "4. Never commit keys to version control"
    Write-Host "5. Restrict access to keys using IAM policies"
    Write-Host "6. Enable audit logging for key access"
    Write-Host "7. Backup keys securely in case of emergency"
    Write-Host ""
    Write-Host "For production deployment:" -ForegroundColor Yellow
    Write-Host "- Use environment variables or secrets management"
    Write-Host "- Enable file-system encryption (BitLocker on Windows)"
    Write-Host "- Configure PostgreSQL SSL/TLS"
    Write-Host "- Implement key rotation strategy"
    Write-Host ""

} catch {
    Write-Host "Error generating keys: $_" -ForegroundColor Red
    exit 1
}
