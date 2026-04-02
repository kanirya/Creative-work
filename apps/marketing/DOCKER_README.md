# Marketing Site Docker Configuration

This directory contains the production-ready Dockerfile for the EduPilot Marketing Site.

## Architecture

The Dockerfile uses a multi-stage build approach:

1. **Dependencies Stage**: Installs npm dependencies
2. **Builder Stage**: Builds the Next.js application as static export
3. **Production Stage**: Serves static files with nginx

## Features

- **Static export**: Next.js builds to static HTML/CSS/JS files
- **nginx only**: Lightweight production image with only nginx
- **Security**: Runs as non-root user (appuser:1000)
- **Health checks**: Built-in health check endpoint
- **Compression**: gzip compression for all text-based assets
- **Caching**: Aggressive caching for static assets (1 year for immutable files)
- **SEO optimized**: Proper headers and routing for search engines

## Building the Image

From the repository root:

```bash
docker build -f apps/marketing/Dockerfile -t edupilot-marketing:latest .
```

## Running the Container

```bash
docker run -d \
  -p 80:80 \
  --name edupilot-marketing \
  edupilot-marketing:latest
```

## Ports

- **80**: nginx web server (exposed)

## Health Check

The container includes a health check that pings the root path every 30 seconds.

## nginx Configuration

The nginx configuration includes:

- Static file serving from `/usr/share/nginx/html`
- Aggressive caching for `_next/static/` (1 year)
- Moderate caching for images and assets (1 day)
- Security headers (CSP, X-Frame-Options, etc.)
- gzip compression for text-based assets
- SPA routing support (serves index.html for all routes)

## Static Export

The marketing site uses Next.js static export (`output: 'export'`), which means:

- All pages are pre-rendered at build time
- No Node.js server required in production
- Extremely fast page loads
- Can be served from any static hosting service
- Perfect for marketing/landing pages

## Production Considerations

1. Use a CDN for global distribution
2. Configure proper DNS and SSL/TLS certificates
3. Set up monitoring for uptime and performance
4. Consider image optimization and lazy loading
5. Implement analytics and tracking
6. Regular security updates for nginx base image
