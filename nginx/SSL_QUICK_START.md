# SSL/TLS Quick Start Guide

Quick reference for setting up SSL/TLS encryption in EduPilot.

## Development Setup (5 minutes)

Self-signed certificates for local testing:

```bash
# 1. Generate certificates
cd nginx
./setup-ssl-certificates.sh

# 2. Start services
cd ..
docker-compose up -d

# 3. Test SSL
cd nginx
./test-ssl.sh local
```

**Access services:**
- API: https://localhost:443/api/health
- Web App: https://localhost:443
- Marketing: https://localhost:443

**Note:** Browser will show certificate warnings (expected for self-signed certs).

## Production Setup (15 minutes)

Let's Encrypt certificates for production:

```bash
# 1. Prerequisites
# - Domain DNS points to server IP
# - Ports 80 and 443 open
# - Update email in setup-letsencrypt.sh

# 2. Generate Let's Encrypt certificates
cd nginx
./setup-letsencrypt.sh

# 3. Start production services
cd ..
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 4. Test SSL
cd nginx
./test-ssl.sh remote

# 5. Verify automatic renewal
crontab -l | grep renew-certificates
```

**Automatic renewal:** Certificates renew daily at 2 AM.

## Testing

```bash
# Quick test
curl -v https://api.edupilot.com/health

# Full SSL test
cd nginx
./test-ssl.sh remote

# Check certificate expiry
openssl x509 -in ssl/api.edupilot.com/fullchain.pem -noout -dates
```

## Troubleshooting

**nginx won't start:**
```bash
# Check config
docker exec edupilot-nginx nginx -t

# Check certificates exist
ls -la nginx/ssl/api.edupilot.com/

# Regenerate self-signed certs
cd nginx && ./setup-ssl-certificates.sh
```

**Certificate renewal fails:**
```bash
# Check renewal log
tail -f nginx/renewal.log

# Test renewal
sudo certbot renew --dry-run

# Manual renewal
cd nginx && ./renew-certificates.sh
```

## Files

- `setup-ssl-certificates.sh` - Generate self-signed certs (dev)
- `setup-letsencrypt.sh` - Set up Let's Encrypt (prod)
- `renew-certificates.sh` - Renew certificates
- `test-ssl.sh` - Test SSL configuration
- `SSL_SETUP.md` - Detailed setup guide
- `TLS_IMPLEMENTATION.md` - Complete implementation docs

## Requirements

✅ **Requirement 16.1:** All data in transit encrypted using TLS 1.3

**Validation:**
```bash
# Verify TLS 1.3
openssl s_client -connect api.edupilot.com:443 -tls1_3 | grep Protocol

# Expected: Protocol  : TLSv1.3
```

## Support

- Detailed docs: `nginx/SSL_SETUP.md`
- Implementation: `nginx/TLS_IMPLEMENTATION.md`
- nginx docs: `nginx/README.md`
