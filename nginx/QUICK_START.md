# Nginx Reverse Proxy - Quick Start Guide

## Development Setup (5 minutes)

```bash
# 1. Start all services
docker-compose up -d

# 2. Access services directly (no nginx)
# API: http://localhost:5000
# Web: http://localhost:3000
# Marketing: http://localhost:3001
```

## Production Setup (15 minutes)

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with production values

# 2. Start services
docker-compose up -d

# 3. Start nginx reverse proxy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d nginx

# 4. Setup SSL certificates (requires DNS configured)
cd nginx
chmod +x setup-ssl.sh
SSL_EMAIL=admin@edupilot.com ./setup-ssl.sh

# 5. Reload nginx with SSL
docker exec edupilot-nginx nginx -s reload

# 6. Test setup
chmod +x test-nginx.sh
./test-nginx.sh
```

## Access Production Services

- API: https://api.edupilot.com
- Web App: https://app.edupilot.com
- Marketing: https://edupilot.com

## Common Commands

```bash
# View logs
docker logs -f edupilot-nginx

# Test configuration
docker exec edupilot-nginx nginx -t

# Reload configuration
docker exec edupilot-nginx nginx -s reload

# Restart nginx
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx

# Stop nginx
docker-compose -f docker-compose.yml -f docker-compose.prod.yml stop nginx
```

## Troubleshooting

### Can't connect to services
```bash
# Check if services are running
docker-compose ps

# Check nginx logs
docker logs edupilot-nginx
```

### SSL certificate errors
```bash
# Verify certificates exist
docker exec edupilot-nginx ls -la /etc/nginx/ssl/

# Re-run SSL setup
cd nginx && ./setup-ssl.sh
```

### Rate limiting issues
```bash
# View rate limit logs
docker exec edupilot-nginx grep "limiting" /var/log/nginx/error.log
```

## Next Steps

- Read [README.md](README.md) for detailed configuration
- Read [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- Set up monitoring and alerting
- Configure automatic SSL renewal

## Support

- Check logs: `docker logs edupilot-nginx`
- Run tests: `./nginx/test-nginx.sh`
- Review documentation in nginx/ directory
