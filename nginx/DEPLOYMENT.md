# Nginx Reverse Proxy Deployment Guide

This guide covers deploying the EduPilot nginx reverse proxy in both development and production environments.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Development Deployment](#development-deployment)
3. [Production Deployment](#production-deployment)
4. [SSL Certificate Setup](#ssl-certificate-setup)
5. [Configuration Updates](#configuration-updates)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required
- Docker 20.10+
- Docker Compose 2.0+
- Domain names pointing to your server (for production)
- Ports 80 and 443 available

### Recommended
- At least 2GB RAM
- 2 CPU cores
- 20GB disk space

## Development Deployment

Development deployment uses self-signed certificates and exposes services directly for easier debugging.

### Step 1: Start Services Without Nginx

```bash
# Start all backend services and databases
docker-compose up -d postgres redis api-gateway ai-agent lms-scraper transcription scheduler

# Wait for services to be healthy
docker-compose ps
```

### Step 2: Start Frontend Services

```bash
# Start web and marketing apps
docker-compose up -d web marketing
```

### Step 3: Start Nginx (Optional for Development)

```bash
# Start nginx reverse proxy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d nginx
```

### Access Services

**Without Nginx (Direct Access):**
- API Gateway: http://localhost:5000
- Web App: http://localhost:3000
- Marketing: http://localhost:3001
- PostgreSQL: localhost:5432
- Redis: localhost:6379

**With Nginx:**
- All services: https://localhost (with self-signed certificate warning)

### Testing

```bash
# Test nginx configuration
cd nginx
chmod +x test-nginx.sh
./test-nginx.sh
```

## Production Deployment

Production deployment uses Let's Encrypt certificates and routes all traffic through nginx.

### Step 1: DNS Configuration

Ensure your domain names point to your server:

```bash
# Check DNS records
dig api.edupilot.com
dig app.edupilot.com
dig edupilot.com
dig www.edupilot.com
```

All should return your server's IP address.

### Step 2: Environment Configuration

Create a `.env` file in the project root:

```bash
# Database
POSTGRES_DB=edupilot
POSTGRES_USER=edupilot
POSTGRES_PASSWORD=<strong-password>

# JWT
JWT_SECRET_KEY=<generate-strong-secret>
JWT_ISSUER=EduPilot
JWT_AUDIENCE=EduPilot

# OpenAI
OPENAI_API_KEY=<your-openai-key>

# SSL
SSL_EMAIL=admin@edupilot.com

# Environment
ASPNETCORE_ENVIRONMENT=Production
NODE_ENV=production
```

### Step 3: Start Backend Services

```bash
# Start databases first
docker-compose up -d postgres redis

# Wait for databases to be healthy
docker-compose ps

# Start backend services
docker-compose up -d api-gateway ai-agent lms-scraper transcription scheduler
```

### Step 4: Start Frontend Services

```bash
# Build and start frontend apps
docker-compose up -d web marketing
```

### Step 5: Start Nginx with HTTP Only (for Let's Encrypt)

Initially, start nginx with HTTP only to allow Let's Encrypt verification:

```bash
# Temporarily modify nginx.conf to comment out SSL server blocks
# Or use a separate nginx-http.conf for initial setup

docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d nginx
```

### Step 6: Obtain SSL Certificates

```bash
cd nginx
chmod +x setup-ssl.sh

# For staging (test) certificates
STAGING=1 SSL_EMAIL=admin@edupilot.com ./setup-ssl.sh

# For production certificates (after testing)
SSL_EMAIL=admin@edupilot.com ./setup-ssl.sh
```

### Step 7: Update Nginx Configuration

After obtaining certificates, update nginx to use them:

```bash
# Reload nginx with SSL configuration
docker exec edupilot-nginx nginx -s reload

# Or restart nginx
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx
```

### Step 8: Verify Deployment

```bash
# Test all endpoints
curl -I https://api.edupilot.com/health
curl -I https://app.edupilot.com
curl -I https://edupilot.com

# Run comprehensive tests
cd nginx
./test-nginx.sh
```

## SSL Certificate Setup

### Automatic Renewal

Set up automatic certificate renewal with cron:

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at midnight)
0 0 * * * docker run --rm -v nginx-ssl:/etc/letsencrypt -v certbot-webroot:/var/www/certbot certbot/certbot renew --quiet && docker exec edupilot-nginx nginx -s reload
```

### Manual Renewal

```bash
# Renew all certificates
docker run --rm \
  -v nginx-ssl:/etc/letsencrypt \
  -v certbot-webroot:/var/www/certbot \
  certbot/certbot renew

# Reload nginx
docker exec edupilot-nginx nginx -s reload
```

### Certificate Verification

```bash
# Check certificate expiry
docker run --rm \
  -v nginx-ssl:/etc/letsencrypt \
  certbot/certbot certificates

# Test SSL configuration
openssl s_client -connect api.edupilot.com:443 -servername api.edupilot.com
```

## Configuration Updates

### Updating Nginx Configuration

1. Edit `nginx/nginx.conf`
2. Test configuration:
   ```bash
   docker exec edupilot-nginx nginx -t
   ```
3. Reload nginx:
   ```bash
   docker exec edupilot-nginx nginx -s reload
   ```

### Adding New Domains

1. Update DNS records
2. Update `nginx/nginx.conf` with new server block
3. Obtain SSL certificate:
   ```bash
   docker run -it --rm \
     -v nginx-ssl:/etc/letsencrypt \
     -v certbot-webroot:/var/www/certbot \
     certbot/certbot certonly \
     --webroot \
     --webroot-path=/var/www/certbot \
     --email admin@edupilot.com \
     --agree-tos \
     -d new-domain.edupilot.com
   ```
4. Reload nginx

### Adjusting Rate Limits

Edit `nginx/nginx.conf`:

```nginx
# Change rate limit
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=200r/m;  # Increased from 100r/m

# Apply to location
location /api/ {
    limit_req zone=api_limit burst=40 nodelay;  # Increased burst
    # ...
}
```

Then reload:
```bash
docker exec edupilot-nginx nginx -s reload
```

## Monitoring and Maintenance

### View Logs

```bash
# Container logs
docker logs -f edupilot-nginx

# Access logs
docker exec edupilot-nginx tail -f /var/log/nginx/access.log

# Error logs
docker exec edupilot-nginx tail -f /var/log/nginx/error.log

# Filter for errors only
docker exec edupilot-nginx grep "error" /var/log/nginx/error.log
```

### Monitor Rate Limiting

```bash
# Count rate limit errors
docker exec edupilot-nginx grep "limiting requests" /var/log/nginx/error.log | wc -l

# Show recent rate limit events
docker exec edupilot-nginx grep "limiting requests" /var/log/nginx/error.log | tail -20
```

### Check Upstream Health

```bash
# Test connectivity to upstreams
docker exec edupilot-nginx nc -zv api-gateway 8080
docker exec edupilot-nginx nc -zv web 80
docker exec edupilot-nginx nc -zv marketing 80
```

### Performance Metrics

```bash
# Request count
docker exec edupilot-nginx wc -l /var/log/nginx/access.log

# Response time analysis (requires awk)
docker exec edupilot-nginx awk '{print $NF}' /var/log/nginx/access.log | \
  awk '{sum+=$1; count++} END {print "Average:", sum/count, "seconds"}'

# Status code distribution
docker exec edupilot-nginx awk '{print $9}' /var/log/nginx/access.log | \
  sort | uniq -c | sort -rn
```

### Log Rotation

Nginx automatically rotates logs. To manually rotate:

```bash
# Send USR1 signal to reopen log files
docker exec edupilot-nginx nginx -s reopen
```

## Troubleshooting

### Nginx Won't Start

```bash
# Check configuration syntax
docker exec edupilot-nginx nginx -t

# Check logs
docker logs edupilot-nginx

# Check if ports are in use
netstat -tulpn | grep -E ':(80|443)'
```

### SSL Certificate Errors

```bash
# Verify certificate files exist
docker exec edupilot-nginx ls -la /etc/nginx/ssl/api.edupilot.com/

# Check certificate validity
docker exec edupilot-nginx openssl x509 -in /etc/nginx/ssl/api.edupilot.com/fullchain.pem -text -noout

# Test SSL connection
openssl s_client -connect api.edupilot.com:443 -servername api.edupilot.com
```

### Rate Limiting Too Aggressive

Temporarily disable rate limiting for testing:

```nginx
# Comment out limit_req in nginx.conf
location /api/ {
    # limit_req zone=api_limit burst=20 nodelay;
    proxy_pass http://api_gateway;
    # ...
}
```

Then reload:
```bash
docker exec edupilot-nginx nginx -s reload
```

### Upstream Connection Errors

```bash
# Check if upstream services are running
docker-compose ps

# Check if services are healthy
docker-compose ps | grep healthy

# Test direct connection to upstream
curl http://localhost:5000/health  # API Gateway
curl http://localhost:3000/api/health  # Web App
```

### High Memory Usage

```bash
# Check nginx memory usage
docker stats edupilot-nginx

# Reduce worker connections if needed
# Edit nginx.conf:
events {
    worker_connections 1024;  # Reduced from 2048
}
```

### 502 Bad Gateway

Common causes:
1. Upstream service is down
2. Upstream service is not responding
3. Timeout too short

```bash
# Check upstream health
docker-compose ps

# Increase timeout in nginx.conf
location /api/ {
    proxy_read_timeout 120s;  # Increased from 60s
    # ...
}
```

### 504 Gateway Timeout

```bash
# Increase timeouts in nginx.conf
location /api/ {
    proxy_connect_timeout 30s;
    proxy_send_timeout 120s;
    proxy_read_timeout 120s;
    # ...
}

# Reload nginx
docker exec edupilot-nginx nginx -s reload
```

## Security Checklist

- [ ] SSL certificates are from Let's Encrypt (not self-signed)
- [ ] HSTS header is enabled
- [ ] Rate limiting is configured
- [ ] Security headers are present
- [ ] Firewall allows only ports 80 and 443
- [ ] fail2ban or similar is configured
- [ ] Log monitoring is set up
- [ ] Automatic certificate renewal is configured
- [ ] Strong passwords in .env file
- [ ] .env file is not committed to git

## Performance Checklist

- [ ] Gzip compression is enabled
- [ ] Static assets have cache headers
- [ ] HTTP/2 is enabled
- [ ] Keepalive connections are configured
- [ ] Worker processes match CPU cores
- [ ] Buffer sizes are appropriate
- [ ] Upstream keepalive is configured

## Backup and Recovery

### Backup SSL Certificates

```bash
# Backup certificates
docker run --rm \
  -v nginx-ssl:/etc/letsencrypt \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/ssl-certificates-$(date +%Y%m%d).tar.gz /etc/letsencrypt
```

### Restore SSL Certificates

```bash
# Restore certificates
docker run --rm \
  -v nginx-ssl:/etc/letsencrypt \
  -v $(pwd)/backup:/backup \
  alpine tar xzf /backup/ssl-certificates-YYYYMMDD.tar.gz -C /
```

### Backup Configuration

```bash
# Backup nginx configuration
cp nginx/nginx.conf nginx/nginx.conf.backup-$(date +%Y%m%d)
```

## Support

For issues or questions:
1. Check logs: `docker logs edupilot-nginx`
2. Run tests: `./nginx/test-nginx.sh`
3. Review this guide
4. Check nginx documentation: https://nginx.org/en/docs/
