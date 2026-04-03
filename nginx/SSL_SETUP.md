# SSL/TLS Certificate Setup Guide

This guide covers setting up SSL/TLS encryption for the EduPilot system using TLS 1.3.

## Overview

The EduPilot system uses nginx as a reverse proxy with TLS 1.3 encryption for all HTTPS traffic. This ensures all data transmission is encrypted according to Requirement 16.1.

## Development Setup (Self-Signed Certificates)

For local development and testing, use self-signed certificates:

```bash
# Run the setup script
bash nginx/setup-ssl-certificates.sh
```

This generates certificates for:
- `api.edupilot.com` (API Gateway)
- `app.edupilot.com` (Student Web App)
- `edupilot.com` (Marketing Site)

**Note:** Self-signed certificates will show browser warnings. This is expected for development.

## Production Setup (Let's Encrypt)

For production deployment, use Let's Encrypt for trusted SSL certificates:

### Prerequisites

1. Domain names must point to your server's IP address
2. Ports 80 and 443 must be open in firewall
3. nginx must be running

### Installation

```bash
# Install certbot
# Ubuntu/Debian:
sudo apt-get update
sudo apt-get install certbot

# CentOS/RHEL:
sudo yum install certbot

# macOS:
brew install certbot
```

### Generate Certificates

```bash
# Run the Let's Encrypt setup script
bash nginx/setup-letsencrypt.sh
```

This script will:
1. Generate certificates for all domains
2. Copy certificates to nginx SSL directory
3. Set up automatic renewal via cron job

### Manual Renewal

Certificates are automatically renewed daily at 2 AM. To manually renew:

```bash
# Renew all certificates
bash nginx/renew-certificates.sh

# Test renewal (dry run)
sudo certbot renew --dry-run
```

## TLS Configuration

The nginx configuration (`nginx/nginx.conf`) is configured with:

### TLS Protocols
- **TLS 1.3** (preferred)
- **TLS 1.2** (fallback for compatibility)

### Cipher Suites
Strong cipher suites only:
```
ECDHE-ECDSA-AES128-GCM-SHA256
ECDHE-RSA-AES128-GCM-SHA256
ECDHE-ECDSA-AES256-GCM-SHA384
ECDHE-RSA-AES256-GCM-SHA384
ECDHE-ECDSA-CHACHA20-POLY1305
ECDHE-RSA-CHACHA20-POLY1305
DHE-RSA-AES128-GCM-SHA256
DHE-RSA-AES256-GCM-SHA384
```

### Security Features
- **HSTS** (HTTP Strict Transport Security) with 1-year max-age
- **OCSP Stapling** for certificate validation
- **Session Caching** for performance
- **Perfect Forward Secrecy** via ECDHE/DHE key exchange

## Certificate Locations

Certificates are stored in:
```
nginx/ssl/
├── api.edupilot.com/
│   ├── fullchain.pem
│   ├── privkey.pem
│   └── chain.pem
├── app.edupilot.com/
│   ├── fullchain.pem
│   ├── privkey.pem
│   └── chain.pem
└── edupilot.com/
    ├── fullchain.pem
    ├── privkey.pem
    └── chain.pem
```

## Verification

### Test TLS Configuration

```bash
# Test TLS 1.3 support
openssl s_client -connect api.edupilot.com:443 -tls1_3

# Check certificate details
openssl s_client -connect api.edupilot.com:443 -showcerts

# Test with curl
curl -v https://api.edupilot.com/health
```

### Online Tools

- **SSL Labs**: https://www.ssllabs.com/ssltest/
- **Security Headers**: https://securityheaders.com/

Expected SSL Labs grade: **A+**

## Troubleshooting

### Certificate Not Found

If nginx fails to start with certificate errors:

```bash
# Check certificate files exist
ls -la nginx/ssl/api.edupilot.com/

# Verify permissions
# privkey.pem should be 600
# fullchain.pem and chain.pem should be 644
```

### Let's Encrypt Rate Limits

Let's Encrypt has rate limits:
- 50 certificates per registered domain per week
- 5 duplicate certificates per week

If you hit rate limits, use staging environment for testing:
```bash
certbot certonly --staging --webroot ...
```

### Certificate Expiry

Let's Encrypt certificates expire after 90 days. The automatic renewal cron job should handle this, but you can check:

```bash
# Check certificate expiry
openssl x509 -in nginx/ssl/api.edupilot.com/fullchain.pem -noout -dates

# Check renewal log
cat nginx/renewal.log
```

## Security Best Practices

1. **Keep Private Keys Secure**
   - Never commit private keys to version control
   - Restrict file permissions (600 for privkey.pem)
   - Use separate keys for each environment

2. **Monitor Certificate Expiry**
   - Set up alerts for certificate expiration
   - Test renewal process regularly

3. **Update TLS Configuration**
   - Review cipher suites quarterly
   - Disable deprecated protocols (TLS 1.0, 1.1)
   - Monitor security advisories

4. **Use Strong Key Sizes**
   - Minimum 2048-bit RSA keys
   - Prefer 4096-bit for production

## Compliance

This SSL/TLS setup satisfies:
- **Requirement 16.1**: All data in transit encrypted using TLS 1.3
- **FERPA Compliance**: Secure transmission of student data
- **Industry Standards**: Follows OWASP and NIST guidelines

## References

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [OWASP TLS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)
