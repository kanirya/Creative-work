# EduPilot Nginx Reverse Proxy

This directory contains the nginx reverse proxy configuration for the EduPilot system. The reverse proxy sits in front of all services and handles SSL/TLS termination, rate limiting, request routing, and security headers.

## Features

### SSL/TLS Configuration
- **TLS 1.3 and TLS 1.2** support with modern cipher suites
- **HSTS** (HTTP Strict Transport Security) with 1-year max-age
- **SSL session caching** for improved performance
- **OCSP stapling** for certificate validation
- Self-signed certificates for development (replace with Let's Encrypt in production)

### Rate Limiting
- **API endpoints**: 100 requests per minute per IP
- **Authentication endpoints**: 10 requests per minute per IP (stricter)
- **Connection limiting**: Maximum concurrent connections per IP
- Burst handling with nodelay for better user experience

### Security Headers
- `X-Frame-Options: SAMEORIGIN` - Prevents clickjacking
- `X-Content-Type-Options: nosniff` - Prevents MIME sniffing
- `X-XSS-Protection: 1; mode=block` - XSS protection
- `Referrer-Policy: strict-origin-when-cross-origin` - Referrer control
- `Strict-Transport-Security` - Forces HTTPS
- `Content-Security-Policy` - Restricts resource loading

### Request Routing
- **api.edupilot.com** → API Gateway (port 8080)
- **app.edupilot.com** → Student Web App (port 80)
- **edupilot.com / www.edupilot.com** → Marketing Site (port 80)

### Performance Optimizations
- **Gzip compression** for text-based content
- **Static asset caching** with immutable cache headers
- **HTTP/2** support for multiplexing
- **Keepalive connections** to upstream services
- **Connection pooling** with least_conn load balancing

### Request Buffering
- Client body buffer: 128KB
- Maximum body size: 50MB (for file uploads)
- Proxy buffering enabled for better performance
- Configurable timeouts for different endpoint types

## Architecture

```
Internet
    ↓
[Nginx Reverse Proxy]
    ├── api.edupilot.com → API Gateway (api-gateway:8080)
    ├── app.edupilot.com → Web App (web:80)
    └── edupilot.com → Marketing Site (marketing:80)
```

## Usage

### Development

For development, use the standard docker-compose.yml which exposes services directly:

```bash
docker-compose up -d
```

Services will be available at:
- API Gateway: http://localhost:5000
- Web App: http://localhost:3000
- Marketing: http://localhost:3001

### Production

For production, use docker-compose.prod.yml which includes the nginx reverse proxy:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

All traffic will go through nginx:
- HTTP: Port 80 (redirects to HTTPS)
- HTTPS: Port 443

## SSL Certificate Management

### Development (Self-Signed Certificates)

The Dockerfile automatically generates self-signed certificates for development. These are stored in:
- `/etc/nginx/ssl/api.edupilot.com/`
- `/etc/nginx/ssl/app.edupilot.com/`
- `/etc/nginx/ssl/edupilot.com/`

### Production (Let's Encrypt)

For production, replace self-signed certificates with Let's Encrypt certificates:

1. Install certbot:
```bash
docker run -it --rm \
  -v nginx-ssl:/etc/letsencrypt \
  -v certbot-webroot:/var/www/certbot \
  certbot/certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email admin@edupilot.com \
  --agree-tos \
  --no-eff-email \
  -d api.edupilot.com
```

2. Repeat for other domains (app.edupilot.com, edupilot.com)

3. Set up automatic renewal:
```bash
# Add to crontab
0 0 * * * docker run --rm -v nginx-ssl:/etc/letsencrypt -v certbot-webroot:/var/www/certbot certbot/certbot renew --quiet
```

## Configuration Files

### nginx.conf
Main nginx configuration with:
- HTTP to HTTPS redirect
- Three server blocks (API, Web App, Marketing)
- Rate limiting zones
- Upstream definitions
- SSL/TLS settings

### Dockerfile
Builds nginx image with:
- Alpine Linux base
- Self-signed certificates for development
- Health check configuration

## Rate Limiting Details

### API Endpoints (`/api/`)
- **Rate**: 100 requests per minute per IP
- **Burst**: 20 requests
- **Behavior**: nodelay (immediate processing of burst)

### Authentication Endpoints (`/api/auth`, `/api/login`, `/api/register`)
- **Rate**: 10 requests per minute per IP
- **Burst**: 5 requests
- **Behavior**: nodelay

### Connection Limits
- **API endpoints**: 20 concurrent connections per IP
- **Auth endpoints**: 10 concurrent connections per IP

## Monitoring

### Access Logs
Location: `/var/log/nginx/access.log`

Format includes:
- Client IP and user
- Request details
- Response status and size
- Referrer and user agent
- Request time and upstream times

### Error Logs
Location: `/var/log/nginx/error.log`
Level: `warn`

### Health Check
Endpoint: `http://localhost/health`
- Checks nginx is responding
- Used by Docker healthcheck
- Not logged to access log

## Troubleshooting

### Check nginx configuration syntax
```bash
docker exec edupilot-nginx nginx -t
```

### Reload configuration without downtime
```bash
docker exec edupilot-nginx nginx -s reload
```

### View logs
```bash
# Access logs
docker logs edupilot-nginx

# Nginx access log
docker exec edupilot-nginx tail -f /var/log/nginx/access.log

# Nginx error log
docker exec edupilot-nginx tail -f /var/log/nginx/error.log
```

### Test rate limiting
```bash
# Should succeed for first 100 requests, then rate limit
for i in {1..110}; do
  curl -s -o /dev/null -w "%{http_code}\n" https://api.edupilot.com/api/health
done
```

### Check SSL certificate
```bash
openssl s_client -connect api.edupilot.com:443 -servername api.edupilot.com
```

## Security Considerations

1. **Replace self-signed certificates** with real certificates in production
2. **Update CSP headers** based on your actual resource requirements
3. **Configure firewall** to only allow traffic on ports 80 and 443
4. **Enable fail2ban** or similar to block malicious IPs
5. **Monitor rate limit violations** and adjust thresholds as needed
6. **Keep nginx updated** to latest stable version
7. **Review access logs** regularly for suspicious activity

## Performance Tuning

### Worker Processes
Default: `auto` (matches CPU cores)

For high traffic, consider:
```nginx
worker_processes 4;
worker_connections 4096;
```

### Buffer Sizes
Adjust based on your traffic patterns:
```nginx
client_body_buffer_size 256k;  # For larger uploads
proxy_buffers 16 8k;           # More buffers for high concurrency
```

### Caching
Consider adding proxy caching for frequently accessed content:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g;
```

## Requirements Validation

This configuration satisfies:
- **Requirement 14.2**: nginx as reverse proxy for routing traffic
- **Requirement 16.1**: TLS 1.3 encryption for all data in transit
- **Requirement 11.3**: Rate limiting (100 requests/minute per student)

## References

- [Nginx Documentation](https://nginx.org/en/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
