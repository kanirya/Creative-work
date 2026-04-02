# Student Web App Docker Configuration

This directory contains the production-ready Dockerfile for the EduPilot Student Web App.

## Architecture

The Dockerfile uses a multi-stage build approach:

1. **Dependencies Stage**: Installs npm dependencies for the monorepo workspace
2. **Builder Stage**: Builds the Next.js application with standalone output
3. **Production Stage**: Runs nginx as reverse proxy with Next.js server

## Features

- **Multi-stage build**: Optimized image size by separating build and runtime dependencies
- **nginx reverse proxy**: Handles static file caching and request routing
- **Security**: Runs as non-root user (appuser:1000)
- **Health checks**: Built-in health check endpoint
- **Compression**: gzip compression for static assets
- **Caching**: Aggressive caching for static files, moderate for dynamic content

## Building the Image

From the repository root:

```bash
docker build -f apps/web/Dockerfile -t edupilot-web:latest .
```

## Running the Container

```bash
docker run -d \
  -p 80:80 \
  -e NEXT_PUBLIC_API_URL=http://api-gateway:5000 \
  --name edupilot-web \
  edupilot-web:latest
```

## Environment Variables

- `NEXT_PUBLIC_API_URL`: API Gateway URL (default: http://localhost:5000)

## Ports

- **3000**: Next.js server (internal)
- **80**: nginx reverse proxy (exposed)

## Health Check

The container includes a health check that pings `/api/health` every 30 seconds.

## nginx Configuration

The nginx configuration includes:

- Static file caching with immutable headers for `_next/static/`
- Proxy pass to Next.js server for dynamic routes
- Security headers (X-Frame-Options, X-Content-Type-Options, etc.)
- gzip compression for text-based assets

## Production Considerations

1. Use environment-specific API URLs
2. Configure proper logging and monitoring
3. Set up SSL/TLS termination at load balancer level
4. Consider using a CDN for static assets
5. Monitor container resource usage and scale horizontally as needed
