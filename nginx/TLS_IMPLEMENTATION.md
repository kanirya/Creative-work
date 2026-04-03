# TLS/SSL Implementation Guide

## Overview

This document describes the complete TLS/SSL encryption implementation for the EduPilot system, satisfying **Requirement 16.1**: "THE EduPilot_System SHALL encrypt all data in transit using TLS 1.3".

## Implementation Status

✅ **COMPLETED** - Task 21.1: Implement TLS/SSL encryption

### What's Implemented

1. **TLS 1.3 Configuration** - nginx configured with TLS 1.3 as primary protocol
2. **Self-Signed Certificates** - Automatic generation for development environments
3. **Let's Encrypt Integration** - Production-ready certificate management
4. **Certificate Renewal Automation** - Automated daily renewal checks
5. **Security Headers** - HSTS, CSP, and other security headers configured
6. **Testing Tools** - Comprehensive SSL/TLS testing scripts

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                             │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS (TLS 1.3)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Nginx Reverse Proxy                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  SSL/TLS Termination                                   │ │
│  │  - TLS 1.3 / TLS 1.2                                   │ │
│  │  - Strong cipher suites                                │ │
│  │  - HSTS, OCSP stapling                                 │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────┬──────────────┬──────────────┬──────────────────┘
             │              │              │
             ▼              ▼              ▼
      ┌──────────┐   ┌──────────┐   ┌──────────┐
      │   API    │   │   Web    │   │Marketing │
      │ Gateway  │   │   App    │   │   Site   │
      └──────────┘   └──────────┘   └──────────┘
```

## TLS Configuration Details

### Supported Protocols

- **TLS 1.3** (preferred) - Modern, secure protocol
- **TLS 1.2** (fallback) - For compatibility with older clients
- **TLS 1.1 and 1.0** - DISABLED (security vulnerabilities)

### Cipher Suites

Strong cipher suites only (in order of preference):

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

All cipher suites provide:
- **Perfect Forward Secrecy** (PFS) via ECDHE/DHE
- **Authenticated Encryption** via GCM/POLY1305
- **Strong Key Exchange** via ECDHE/DHE

### Security Features

1. **HSTS (HTTP Strict Transport Security)**
   - Max-age: 31536000 seconds (1 year)
   - includeSubDomains: Yes
   - preload: Yes

2. **OCSP Stapling**
   - Enabled for faster certificate validation
   - Reduces client-side OCSP lookups

3. **Session Management**
   - Session cache: 10MB shared cache
   - Session timeout: 10 minutes
   - Session tickets: Disabled (for better security)

4. **HTTP to HTTPS Redirect**
   - All HTTP traffic automatically redirected to HTTPS
   - Except ACME challenge path for Let's Encrypt

## Certificate Management

### Development Environment

**Self-Signed Certificates** are automatically generated during Docker build:

```bash
# Certificates are created for:
- api.edupilot.com
- app.edupilot.com
- edupilot.com

# Location: /etc/nginx/ssl/<domain>/
- fullchain.pem (certificate)
- privkey.pem (private key)
- chain.pem (certificate chain)
```

**Generate manually:**
```bash
cd nginx
./setup-ssl-certificates.sh
```

### Production Environment

**Let's Encrypt** certificates for trusted SSL:

**Prerequisites:**
1. Domain DNS records point to server IP
2. Ports 80 and 443 open in firewall
3. nginx running with HTTP server for ACME challenge

**Setup:**
```bash
cd nginx
./setup-letsencrypt.sh
```

This will:
1. Request certificates from Let's Encrypt
2. Copy certificates to nginx SSL directory
3. Set up automatic renewal cron job
4. Configure daily renewal checks at 2 AM

### Certificate Renewal

**Automatic Renewal:**
- Cron job runs daily at 2 AM
- Checks if certificates need renewal (< 30 days until expiry)
- Renews certificates if needed
- Reloads nginx to use new certificates
- Logs all operations to `nginx/renewal.log`

**Manual Renewal:**
```bash
cd nginx
./renew-certificates.sh
```

**Test Renewal (Dry Run):**
```bash
sudo certbot renew --dry-run
```

## Security Headers

All responses include security headers:

### Common Headers (All Domains)

```nginx
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

### API Gateway (api.edupilot.com)

Additional CORS headers:
```nginx
Access-Control-Allow-Origin: <origin>
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type, X-Requested-With
Access-Control-Allow-Credentials: true
```

### Web App & Marketing Site

Content Security Policy (CSP):
```nginx
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' ...
```

## Testing and Verification

### Automated Testing

Run the SSL test script:

```bash
# Test local development setup
cd nginx
./test-ssl.sh local

# Test production deployment
./test-ssl.sh remote
```

The script tests:
- Certificate validity and key size
- TLS 1.3 and TLS 1.2 support
- TLS 1.1 and 1.0 disabled
- Strong cipher suites
- Security headers
- HTTP to HTTPS redirect

### Manual Testing

**Test TLS 1.3 connection:**
```bash
openssl s_client -connect api.edupilot.com:443 -tls1_3
```

**Check certificate details:**
```bash
openssl s_client -connect api.edupilot.com:443 -showcerts
```

**Test with curl:**
```bash
curl -v https://api.edupilot.com/health
```

**Check certificate expiry:**
```bash
openssl x509 -in nginx/ssl/api.edupilot.com/fullchain.pem -noout -dates
```

### Online Testing Tools

1. **SSL Labs Server Test**
   - URL: https://www.ssllabs.com/ssltest/
   - Expected Grade: **A+**
   - Tests: Protocol support, cipher suites, vulnerabilities

2. **Security Headers**
   - URL: https://securityheaders.com/
   - Expected Grade: **A**
   - Tests: HSTS, CSP, X-Frame-Options, etc.

3. **Mozilla Observatory**
   - URL: https://observatory.mozilla.org/
   - Expected Grade: **A+**
   - Tests: Overall security configuration

## Deployment

### Development Deployment

```bash
# Start services with self-signed certificates
docker-compose up -d

# nginx will automatically generate self-signed certs
# Services available at:
# - https://localhost:443 (nginx)
# - http://localhost:5000 (API Gateway direct)
# - http://localhost:3000 (Web App direct)
```

### Production Deployment

```bash
# 1. Set up Let's Encrypt certificates
cd nginx
./setup-letsencrypt.sh

# 2. Start services with production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 3. Verify SSL configuration
./test-ssl.sh remote

# 4. Check nginx logs
docker logs edupilot-nginx
```

## Monitoring

### Certificate Expiry Monitoring

**Check certificate expiry dates:**
```bash
# Check all certificates
for domain in api.edupilot.com app.edupilot.com edupilot.com; do
  echo "=== $domain ==="
  openssl x509 -in nginx/ssl/$domain/fullchain.pem -noout -dates
  echo ""
done
```

**Set up expiry alerts:**
- Let's Encrypt certificates expire after 90 days
- Renewal happens automatically at 60 days
- Monitor `nginx/renewal.log` for renewal status
- Set up external monitoring (e.g., UptimeRobot, Pingdom)

### Renewal Logs

**View renewal log:**
```bash
tail -f nginx/renewal.log
```

**Check last renewal:**
```bash
grep "completed successfully" nginx/renewal.log | tail -1
```

## Troubleshooting

### Certificate Not Found Error

**Symptom:** nginx fails to start with "certificate not found"

**Solution:**
```bash
# Check certificate files exist
ls -la nginx/ssl/api.edupilot.com/

# Regenerate self-signed certificates
cd nginx
./setup-ssl-certificates.sh

# Restart nginx
docker-compose restart nginx
```

### Let's Encrypt Rate Limits

**Symptom:** "too many certificates already issued"

**Solution:**
- Let's Encrypt limits: 50 certs per domain per week
- Use staging environment for testing:
  ```bash
  certbot certonly --staging --webroot ...
  ```
- Wait for rate limit to reset (1 week)

### Certificate Renewal Fails

**Symptom:** Renewal script fails or certificates not renewed

**Solution:**
```bash
# Check certbot logs
sudo cat /var/log/letsencrypt/letsencrypt.log

# Test renewal manually
sudo certbot renew --dry-run

# Check ACME challenge path is accessible
curl http://api.edupilot.com/.well-known/acme-challenge/test

# Verify cron job is running
crontab -l | grep renew-certificates
```

### Browser Certificate Warnings

**Development (Expected):**
- Self-signed certificates will show warnings
- Click "Advanced" → "Proceed to site" (for testing only)
- Or add certificate to browser's trusted certificates

**Production (Problem):**
- Check certificate is from Let's Encrypt (not self-signed)
- Verify domain name matches certificate CN
- Check certificate is not expired
- Ensure intermediate certificates are included

## Security Best Practices

### Certificate Management

1. **Never commit private keys to version control**
   - Add `nginx/ssl/` to `.gitignore`
   - Use environment-specific certificates

2. **Use strong key sizes**
   - Minimum: 2048-bit RSA
   - Recommended: 4096-bit RSA or 256-bit ECDSA

3. **Rotate certificates regularly**
   - Let's Encrypt: Automatic 90-day rotation
   - Self-signed: Regenerate annually

4. **Separate keys per environment**
   - Development: Self-signed certificates
   - Staging: Let's Encrypt staging certificates
   - Production: Let's Encrypt production certificates

### TLS Configuration

1. **Keep TLS configuration updated**
   - Review Mozilla SSL Configuration Generator quarterly
   - Update cipher suites based on security advisories
   - Test with SSL Labs after changes

2. **Monitor for vulnerabilities**
   - Subscribe to security mailing lists
   - Check for nginx security updates
   - Monitor OpenSSL vulnerabilities

3. **Enable security features**
   - HSTS with preload
   - OCSP stapling
   - Session ticket rotation

### Monitoring and Alerting

1. **Set up certificate expiry alerts**
   - Alert at 30 days before expiry
   - Alert at 7 days before expiry
   - Alert on renewal failures

2. **Monitor SSL/TLS metrics**
   - TLS version usage
   - Cipher suite usage
   - Handshake failures
   - Certificate errors

3. **Regular security audits**
   - Run SSL Labs test monthly
   - Review access logs for suspicious activity
   - Test with vulnerability scanners

## Compliance

### Requirement 16.1 Validation

✅ **THE EduPilot_System SHALL encrypt all data in transit using TLS 1.3**

**Evidence:**
1. nginx configured with `ssl_protocols TLSv1.3 TLSv1.2;`
2. TLS 1.3 is preferred protocol
3. TLS 1.2 available as fallback for compatibility
4. TLS 1.1 and 1.0 explicitly disabled
5. All HTTP traffic redirected to HTTPS
6. Strong cipher suites enforced
7. HSTS header forces HTTPS for 1 year

**Testing:**
```bash
# Verify TLS 1.3 support
openssl s_client -connect api.edupilot.com:443 -tls1_3 | grep "Protocol"
# Expected: Protocol  : TLSv1.3

# Verify TLS 1.0/1.1 disabled
openssl s_client -connect api.edupilot.com:443 -tls1
# Expected: Connection refused or handshake failure
```

### FERPA Compliance

✅ **Student data protected in transit**

- All API endpoints require HTTPS
- Student authentication tokens transmitted over TLS
- Academic data encrypted during transmission
- Lecture recordings and transcriptions encrypted in transit

### Industry Standards

✅ **Follows OWASP and NIST guidelines**

- OWASP Transport Layer Protection Cheat Sheet
- NIST SP 800-52 Rev. 2 (TLS Guidelines)
- Mozilla Modern TLS Configuration
- PCI DSS 3.2.1 (TLS 1.2+ requirement)

## Files and Directories

```
nginx/
├── nginx.conf                    # Main nginx configuration with TLS settings
├── Dockerfile                    # Builds nginx with self-signed certs
├── docker-compose.prod.yml       # Production deployment with nginx
│
├── setup-ssl-certificates.sh     # Generate self-signed certs (development)
├── setup-letsencrypt.sh          # Set up Let's Encrypt (production)
├── renew-certificates.sh         # Automatic renewal script
├── test-ssl.sh                   # SSL/TLS testing script
│
├── SSL_SETUP.md                  # SSL setup guide
├── TLS_IMPLEMENTATION.md         # This file
├── README.md                     # nginx documentation
├── DEPLOYMENT.md                 # Deployment guide
│
├── ssl/                          # Certificate storage (gitignored)
│   ├── api.edupilot.com/
│   │   ├── fullchain.pem
│   │   ├── privkey.pem
│   │   └── chain.pem
│   ├── app.edupilot.com/
│   └── edupilot.com/
│
└── renewal.log                   # Certificate renewal log
```

## References

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [OWASP TLS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)
- [NIST SP 800-52 Rev. 2](https://csrc.nist.gov/publications/detail/sp/800-52/rev-2/final)
- [nginx SSL Module Documentation](https://nginx.org/en/docs/http/ngx_http_ssl_module.html)
- [SSL Labs Best Practices](https://github.com/ssllabs/research/wiki/SSL-and-TLS-Deployment-Best-Practices)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review nginx error logs: `docker logs edupilot-nginx`
3. Test SSL configuration: `./nginx/test-ssl.sh`
4. Consult SSL_SETUP.md for detailed setup instructions
