# Client Apps Docker Configuration Summary

This document summarizes the Docker configuration for EduPilot client applications.

## Overview

Production-ready Dockerfiles have been created for:

1. **Student Web App** (`apps/web/`) - Next.js application with nginx reverse proxy
2. **Marketing Site** (`apps/marketing/`) - Static Next.js export served by nginx

## Architecture Decisions

### Student Web App (apps/web)

**Approach**: Multi-stage build with Next.js standalone + nginx reverse proxy

**Rationale**:
- Next.js standalone output provides optimized server bundle
- nginx handles static file caching and compression
- Separation of concerns: nginx for static assets, Node.js for dynamic routes
- Better performance under load with nginx buffering

**Stages**:
1. **deps**: Install npm dependencies for monorepo workspace
2. **builder**: Build Next.js application with standalone output
3. **runner**: nginx + Node.js runtime serving the application

**Key Features**:
- Runs on ports 3000 (Next.js) and 80 (nginx)
- Health check endpoint at `/api/health`
- Aggressive caching for `_next/static/` (immutable)
- Security headers (X-Frame-Options, CSP, etc.)
- Non-root user (appuser:1000)
- gzip compression enabled

### Marketing Site (apps/marketing)

**Approach**: Multi-stage build with static export + nginx only

**Rationale**:
- Marketing site is purely static content (no dynamic routes)
- Static export eliminates Node.js runtime overhead
- Smaller image size (nginx alpine only)
- Faster page loads with pre-rendered HTML
- Can be served from CDN or static hosting

**Stages**:
1. **deps**: Install npm dependencies
2. **builder**: Build Next.js static export to `out/` directory
3. **runner**: nginx alpine serving static files

**Key Features**:
- Runs on port 80 only (no Node.js server)
- Static files served from `/usr/share/nginx/html`
- Aggressive caching (1 year for immutable assets)
- SEO-optimized headers and routing
- Non-root user (appuser:1000)
- gzip compression enabled

## Files Created

### Student Web App
- `apps/web/Dockerfile` - Multi-stage Dockerfile
- `apps/web/nginx.conf` - nginx reverse proxy configuration
- `apps/web/.dockerignore` - Build optimization
- `apps/web/DOCKER_README.md` - Documentation
- `apps/web/src/app/api/health/route.ts` - Health check endpoint

### Marketing Site
- `apps/marketing/Dockerfile` - Multi-stage Dockerfile
- `apps/marketing/nginx.conf` - nginx static file server configuration
- `apps/marketing/.dockerignore` - Build optimization
- `apps/marketing/DOCKER_README.md` - Documentation

### Configuration Updates
- `apps/web/next.config.js` - Added `output: 'standalone'`
- `docker-compose.yml` - Added `web` and `marketing` services

### Scripts
- `scripts/build-client-apps.sh` - Build script for both apps

## Building Images

### Individual Builds

```bash
# Student Web App
docker build -f apps/web/Dockerfile -t edupilot-web:latest .

# Marketing Site
docker build -f apps/marketing/Dockerfile -t edupilot-marketing:latest .
```

### Using Build Script

```bash
bash scripts/build-client-apps.sh
```

### Using Docker Compose

```bash
docker-compose build web marketing
```

## Running Containers

### Individual Containers

```bash
# Student Web App
docker run -d -p 3000:80 \
  -e NEXT_PUBLIC_API_URL=http://api-gateway:5000 \
  --name edupilot-web \
  edupilot-web:latest

# Marketing Site
docker run -d -p 3001:80 \
  --name edupilot-marketing \
  edupilot-marketing:latest
```

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# Start only client apps
docker-compose up -d web marketing
```

## Health Checks

Both containers include health checks:

- **Student Web App**: `http://localhost:80/api/health`
- **Marketing Site**: `http://localhost:80/`

Health checks run every 30 seconds with 3 retries.

## Security Features

1. **Non-root user**: Both containers run as `appuser:1000`
2. **Security headers**: X-Frame-Options, X-Content-Type-Options, CSP, etc.
3. **TLS ready**: nginx configurations support SSL/TLS termination
4. **Input validation**: nginx request size limits
5. **Minimal attack surface**: Only necessary packages installed

## Performance Optimizations

1. **Multi-stage builds**: Smaller final images
2. **Layer caching**: Optimized Dockerfile layer ordering
3. **gzip compression**: Enabled for text-based assets
4. **Static file caching**: Aggressive caching headers
5. **nginx buffering**: Improved performance under load

## Production Considerations

### Student Web App
- Configure `NEXT_PUBLIC_API_URL` for production API Gateway
- Set up SSL/TLS termination at load balancer
- Monitor Node.js memory usage
- Scale horizontally behind load balancer
- Consider CDN for static assets

### Marketing Site
- Deploy behind CDN (CloudFront, Cloudflare, etc.)
- Configure proper DNS and SSL certificates
- Monitor nginx access logs
- Implement analytics tracking
- Regular security updates for base image

## Monitoring

Both containers expose metrics for monitoring:

- Health check endpoints
- nginx access/error logs
- Container resource usage (CPU, memory)
- Request rates and response times

## Troubleshooting

### Build Issues

```bash
# Check Docker daemon
docker info

# Clean build cache
docker builder prune

# Build with no cache
docker build --no-cache -f apps/web/Dockerfile -t edupilot-web:latest .
```

### Runtime Issues

```bash
# Check container logs
docker logs edupilot-web
docker logs edupilot-marketing

# Check container health
docker inspect --format='{{.State.Health.Status}}' edupilot-web

# Access container shell
docker exec -it edupilot-web sh
```

## Compliance with Requirements

**Requirement 14.1**: Infrastructure and Deployment
- ✅ All services packaged as Docker containers
- ✅ nginx used as reverse proxy for routing traffic
- ✅ Production-ready multi-stage builds
- ✅ Health checks implemented
- ✅ Security best practices (non-root user, minimal images)

## Next Steps

1. Test builds in CI/CD pipeline
2. Configure production environment variables
3. Set up container registry (ECR, Docker Hub, etc.)
4. Implement automated deployment
5. Configure monitoring and alerting
6. Set up SSL/TLS certificates
7. Performance testing under load
