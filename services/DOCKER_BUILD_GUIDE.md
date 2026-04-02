# Docker Build Guide for EduPilot Services

This guide provides instructions for building and running all EduPilot backend services using Docker.

## Overview

All backend services have production-ready Dockerfiles with the following features:

- **Multi-stage builds** (API Gateway) for optimized image size
- **Non-root users** for enhanced security
- **Health checks** for container orchestration
- **Minimal base images** (slim variants) for reduced attack surface
- **Proper .dockerignore** files for faster builds

## Services and Ports

| Service | Port | Technology | Dockerfile Location |
|---------|------|------------|---------------------|
| API Gateway | 8080 | .NET 8 | `services/api-gateway/Dockerfile` |
| AI Agent | 8001 | Python 3.11 + FastAPI | `services/ai-agent/Dockerfile` |
| LMS Scraper | 8002 | Python 3.11 + Playwright | `services/lms-scraper/Dockerfile` |
| Transcription | 8003 | Python 3.11 + Whisper | `services/transcription/Dockerfile` |
| Scheduler | 8004 | Python 3.11 + APScheduler | `services/scheduler/Dockerfile` |

## Building Individual Services

### API Gateway (.NET 8)

```bash
cd services/api-gateway
docker build -t edupilot-api-gateway:latest .
```

**Features:**
- Multi-stage build (SDK → Build → Publish → Runtime)
- Uses official Microsoft .NET 8 images
- Optimized layer caching for dependencies
- Final image size: ~200MB

### AI Agent Service

```bash
cd services/ai-agent
docker build -t edupilot-ai-agent:latest .
```

**Features:**
- Python 3.11 slim base image
- LangChain and OpenAI dependencies
- PostgreSQL client for vector database access

### LMS Scraper Service

```bash
cd services/lms-scraper
docker build -t edupilot-lms-scraper:latest .
```

**Features:**
- Playwright with Chromium browser
- Headless browser automation
- Larger image due to browser dependencies (~1GB)

### Transcription Service

```bash
cd services/transcription
docker build -t edupilot-transcription:latest .
```

**Features:**
- FFmpeg for audio processing
- OpenAI Whisper model support
- Audio storage directory at `/tmp/audio`

### Scheduler Service

```bash
cd services/scheduler
docker build -t edupilot-scheduler:latest .
```

**Features:**
- APScheduler for job management
- Lightweight Python service
- Coordinates other services

## Building All Services with Docker Compose

Build all services at once:

```bash
docker-compose build
```

Build specific service:

```bash
docker-compose build api-gateway
docker-compose build ai-agent
```

Build with no cache (clean build):

```bash
docker-compose build --no-cache
```

## Running Services

### Start all services:

```bash
docker-compose up -d
```

### Start specific services:

```bash
docker-compose up -d postgres redis api-gateway
```

### View logs:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api-gateway
docker-compose logs -f ai-agent
```

### Check service health:

```bash
docker-compose ps
```

### Stop services:

```bash
docker-compose down
```

### Stop and remove volumes:

```bash
docker-compose down -v
```

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Database
POSTGRES_DB=edupilot
POSTGRES_USER=edupilot
POSTGRES_PASSWORD=your_secure_password
DATABASE_URL=postgresql://edupilot:your_secure_password@postgres:5432/edupilot

# Redis
REDIS_URL=redis://redis:6379

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ISSUER=EduPilot
JWT_AUDIENCE=EduPilotClients

# OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Service URLs (internal)
AGENT_SERVICE_URL=http://ai-agent:8001
SCRAPER_SERVICE_URL=http://lms-scraper:8002
TRANSCRIBER_SERVICE_URL=http://transcription:8003
```

## Production Deployment

### Building for Production

1. **Set production environment variables:**

```bash
export ASPNETCORE_ENVIRONMENT=Production
```

2. **Build with production tags:**

```bash
docker build -t edupilot-api-gateway:v1.0.0 ./services/api-gateway
docker build -t edupilot-ai-agent:v1.0.0 ./services/ai-agent
docker build -t edupilot-lms-scraper:v1.0.0 ./services/lms-scraper
docker build -t edupilot-transcription:v1.0.0 ./services/transcription
docker build -t edupilot-scheduler:v1.0.0 ./services/scheduler
```

3. **Push to container registry:**

```bash
# Tag for registry
docker tag edupilot-api-gateway:v1.0.0 registry.example.com/edupilot-api-gateway:v1.0.0

# Push to registry
docker push registry.example.com/edupilot-api-gateway:v1.0.0
```

### Security Best Practices

All Dockerfiles implement:

1. **Non-root users:** Services run as user `appuser` (UID 1000)
2. **Minimal base images:** Using slim variants to reduce attack surface
3. **No secrets in images:** All secrets passed via environment variables
4. **Health checks:** Proper health endpoints for orchestration
5. **Layer optimization:** Dependencies cached separately from code

### Resource Limits

Add resource limits in docker-compose.yml:

```yaml
services:
  api-gateway:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

## Troubleshooting

### Build Issues

**Problem:** Docker build fails with "no space left on device"

```bash
# Clean up Docker system
docker system prune -a --volumes
```

**Problem:** Slow builds

```bash
# Use BuildKit for faster builds
export DOCKER_BUILDKIT=1
docker-compose build
```

### Runtime Issues

**Problem:** Service won't start

```bash
# Check logs
docker-compose logs service-name

# Check health status
docker inspect --format='{{.State.Health.Status}}' container-name
```

**Problem:** Cannot connect to database

```bash
# Verify network
docker network inspect edupilot-network

# Check database is ready
docker-compose exec postgres pg_isready -U edupilot
```

### Health Check Failures

All services expose `/health` endpoints. Test manually:

```bash
# API Gateway
curl http://localhost:5000/health

# AI Agent
curl http://localhost:8001/health

# LMS Scraper
curl http://localhost:8002/health

# Transcription
curl http://localhost:8003/health

# Scheduler
curl http://localhost:8004/health
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Push Docker Images

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to Container Registry
        uses: docker/login-action@v2
        with:
          registry: registry.example.com
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}
      
      - name: Build and push API Gateway
        uses: docker/build-push-action@v4
        with:
          context: ./services/api-gateway
          push: true
          tags: registry.example.com/edupilot-api-gateway:${{ github.sha }}
          cache-from: type=registry,ref=registry.example.com/edupilot-api-gateway:buildcache
          cache-to: type=registry,ref=registry.example.com/edupilot-api-gateway:buildcache,mode=max
```

## Performance Optimization

### Build Cache

Use BuildKit cache mounts for faster Python builds:

```dockerfile
# In Python Dockerfiles
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt
```

### Multi-platform Builds

Build for multiple architectures:

```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -t edupilot-api-gateway:latest \
  ./services/api-gateway
```

## Monitoring

### Container Metrics

```bash
# View resource usage
docker stats

# View specific container
docker stats edupilot-api
```

### Log Aggregation

Configure log drivers in docker-compose.yml:

```yaml
services:
  api-gateway:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Additional Resources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [.NET Docker Documentation](https://docs.microsoft.com/en-us/dotnet/core/docker/)
- [FastAPI Docker Documentation](https://fastapi.tiangolo.com/deployment/docker/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
