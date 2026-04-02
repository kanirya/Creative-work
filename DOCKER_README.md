# EduPilot Docker Deployment Guide

## Quick Start

### Prerequisites

- Docker 20.10+ installed
- Docker Compose 2.0+ installed
- At least 8GB RAM available
- At least 20GB disk space

### 1. Environment Setup

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` and set required values:
- `POSTGRES_PASSWORD`: Secure database password
- `JWT_SECRET_KEY`: 256-bit secret key for JWT tokens
- `OPENAI_API_KEY`: Your OpenAI API key

### 2. Start Services

**Option A: Using Scripts (Recommended)**

Linux/Mac:
```bash
chmod +x scripts/docker-start.sh
./scripts/docker-start.sh
```

Windows PowerShell:
```powershell
.\scripts\docker-start.ps1
```

**Option B: Using Make**

```bash
make start
```

**Option C: Using Docker Compose Directly**

```bash
docker-compose up -d
```

### 3. Verify Services

Check service status:
```bash
docker-compose ps
```

View logs:
```bash
docker-compose logs -f
```

### 4. Access Applications

- **Web App**: http://localhost:3000
- **Marketing Site**: http://localhost:3001
- **API Gateway**: http://localhost:5000
- **API Documentation**: http://localhost:5000/swagger

## Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                             │
│  ┌──────────────┐              ┌──────────────┐            │
│  │   Web App    │              │  Marketing   │            │
│  │  (Port 3000) │              │ (Port 3001)  │            │
│  └──────────────┘              └──────────────┘            │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                    Backend Layer                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           API Gateway (.NET 8)                       │  │
│  │              (Port 5000)                             │  │
│  └──────────────────────────────────────────────────────┘  │
│         │              │              │              │       │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐│
│  │AI Agent  │   │   LMS    │   │Transcr.  │   │Scheduler ││
│  │(8001)    │   │ Scraper  │   │(8003)    │   │(8004)    ││
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘│
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                     Data Layer                               │
│  ┌──────────────┐              ┌──────────────┐            │
│  │  PostgreSQL  │              │    Redis     │            │
│  │  + pgvector  │              │   (Cache)    │            │
│  │  (Port 5432) │              │ (Port 6379)  │            │
│  └──────────────┘              └──────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

## Service Details

### Infrastructure Services

| Service    | Port | Purpose                          | Health Check |
|------------|------|----------------------------------|--------------|
| postgres   | 5432 | Database with vector search      | pg_isready   |
| redis      | 6379 | Caching and session management   | redis-cli    |

### Backend Services

| Service       | Port | Technology        | Purpose                    |
|---------------|------|-------------------|----------------------------|
| api-gateway   | 5000 | .NET 8            | Main API entry point       |
| ai-agent      | 8001 | Python + LangChain| NLP and RAG                |
| lms-scraper   | 8002 | Python + Playwright| LMS data extraction       |
| transcription | 8003 | Python + Whisper  | Audio transcription        |
| scheduler     | 8004 | Python + APScheduler| Task scheduling         |

### Frontend Services

| Service   | Port | Technology      | Purpose              |
|-----------|------|-----------------|----------------------|
| web       | 3000 | Next.js + nginx | Student web app      |
| marketing | 3001 | Next.js + nginx | Marketing website    |

## Common Operations

### Starting Services

```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d postgres redis api-gateway

# Start with rebuild
docker-compose up -d --build

# Start in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Stopping Services

```bash
# Stop all services
docker-compose stop

# Stop specific service
docker-compose stop api-gateway

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes (WARNING: deletes data)
docker-compose down -v
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api-gateway

# Last 100 lines
docker-compose logs --tail=100 api-gateway

# Since timestamp
docker-compose logs --since 2024-01-01T00:00:00 api-gateway
```

### Service Management

```bash
# Restart service
docker-compose restart api-gateway

# Rebuild service
docker-compose build api-gateway
docker-compose up -d api-gateway

# View service status
docker-compose ps

# Execute command in service
docker-compose exec api-gateway bash
```

### Database Operations

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U edupilot edupilot

# Create backup
docker-compose exec postgres pg_dump -U edupilot edupilot > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U edupilot edupilot < backup.sql

# View database logs
docker-compose logs -f postgres
```

### Redis Operations

```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# Monitor Redis commands
docker-compose exec redis redis-cli MONITOR

# View Redis info
docker-compose exec redis redis-cli INFO

# Flush all data (WARNING: deletes all cache)
docker-compose exec redis redis-cli FLUSHALL
```

## Development Workflow

### Hot Reload Development

Use the development compose file for hot reload:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

This enables:
- Volume mounts for source code
- Hot reload for all services
- Debug logging
- Development environment variables

### Building Individual Services

```bash
# Build specific service
docker-compose build api-gateway

# Build without cache
docker-compose build --no-cache api-gateway

# Build with progress
docker-compose build --progress=plain api-gateway
```

### Testing Services

```bash
# Run tests in container
docker-compose exec api-gateway dotnet test

# Run Python tests
docker-compose exec ai-agent pytest

# Run with coverage
docker-compose exec ai-agent pytest --cov=app
```

## Monitoring and Debugging

### Health Checks

```bash
# Check all service health
docker-compose ps

# Inspect specific service health
docker inspect --format='{{json .State.Health}}' edupilot-api-gateway | jq

# Watch health status
watch -n 2 'docker-compose ps'
```

### Resource Usage

```bash
# View resource usage
docker stats

# View specific service
docker stats edupilot-api-gateway

# Export stats to file
docker stats --no-stream > stats.txt
```

### Network Debugging

```bash
# Inspect network
docker network inspect edupilot_edupilot-network

# Test connectivity between services
docker-compose exec api-gateway curl http://ai-agent:8001/health

# View network traffic
docker-compose exec api-gateway tcpdump -i any port 8001
```

### Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect edupilot_postgres-data

# Backup volume
docker run --rm -v edupilot_postgres-data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-backup.tar.gz /data

# Restore volume
docker run --rm -v edupilot_postgres-data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres-backup.tar.gz -C /
```

## Troubleshooting

### Service Won't Start

1. Check logs:
   ```bash
   docker-compose logs service-name
   ```

2. Check health status:
   ```bash
   docker-compose ps
   ```

3. Restart service:
   ```bash
   docker-compose restart service-name
   ```

4. Rebuild and restart:
   ```bash
   docker-compose up -d --build service-name
   ```

### Database Connection Issues

1. Verify postgres is healthy:
   ```bash
   docker-compose ps postgres
   ```

2. Test connection:
   ```bash
   docker-compose exec postgres psql -U edupilot -d edupilot -c "SELECT 1"
   ```

3. Check environment variables:
   ```bash
   docker-compose exec api-gateway env | grep DATABASE
   ```

4. Check network connectivity:
   ```bash
   docker-compose exec api-gateway ping postgres
   ```

### Port Conflicts

If ports are already in use:

1. Check what's using the port:
   ```bash
   # Linux/Mac
   lsof -i :5000
   
   # Windows
   netstat -ano | findstr :5000
   ```

2. Change port in docker-compose.yml:
   ```yaml
   ports:
     - "5001:8080"  # Changed from 5000
   ```

### Out of Memory

1. Check Docker memory limit:
   ```bash
   docker info | grep Memory
   ```

2. Increase Docker memory in Docker Desktop settings

3. Add memory limits to services:
   ```yaml
   services:
     api-gateway:
       deploy:
         resources:
           limits:
             memory: 2G
   ```

### Disk Space Issues

1. Check disk usage:
   ```bash
   docker system df
   ```

2. Clean up unused resources:
   ```bash
   docker system prune -a
   ```

3. Remove old volumes:
   ```bash
   docker volume prune
   ```

## Production Deployment

### Security Checklist

- [ ] Change all default passwords in `.env`
- [ ] Use strong JWT secret key (256-bit)
- [ ] Enable TLS/SSL for external access
- [ ] Restrict exposed ports
- [ ] Use Docker secrets for sensitive data
- [ ] Enable firewall rules
- [ ] Regular security updates

### Performance Optimization

1. **Resource Limits**: Set memory and CPU limits
2. **Scaling**: Use `docker-compose up -d --scale ai-agent=3`
3. **Caching**: Configure Redis with appropriate memory limits
4. **Database**: Tune PostgreSQL configuration
5. **Monitoring**: Set up Prometheus and Grafana

### Backup Strategy

1. **Database**: Daily automated backups
   ```bash
   0 2 * * * docker-compose exec postgres pg_dump -U edupilot edupilot > /backups/db_$(date +\%Y\%m\%d).sql
   ```

2. **Volumes**: Regular volume snapshots
3. **Configuration**: Version control for docker-compose.yml
4. **Disaster Recovery**: Document recovery procedures

### High Availability

1. **Load Balancing**: Add nginx or HAProxy
2. **Database Replication**: Set up PostgreSQL replicas
3. **Redis Cluster**: Use Redis Cluster for HA
4. **Service Redundancy**: Run multiple instances of stateless services

## Environment Variables Reference

### Required Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/edupilot
POSTGRES_DB=edupilot
POSTGRES_USER=edupilot
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_URL=redis://redis:6379

# JWT
JWT_SECRET_KEY=your_256_bit_secret
JWT_ISSUER=EduPilot
JWT_AUDIENCE=EduPilot

# OpenAI
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Optional Variables

```bash
# AWS S3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=ap-south-1
AWS_S3_BUCKET=edupilot-storage

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

## Makefile Commands

If you have `make` installed, you can use these shortcuts:

```bash
make help           # Show all available commands
make start          # Start all services
make stop           # Stop all services
make restart        # Restart all services
make build          # Build all services
make logs           # View logs
make status         # Show service status
make health         # Check health
make dev            # Start in development mode
make clean          # Clean everything (WARNING: deletes data)
```

## Additional Resources

- [Docker Compose Guide](./DOCKER_COMPOSE_GUIDE.md) - Detailed configuration documentation
- [Service Dockerfiles](./services/DOCKER_BUILD_GUIDE.md) - Individual service build guides
- [Client Apps Docker](./apps/DOCKER_QUICK_START.md) - Frontend deployment guide
- [Architecture Design](./design.md) - System architecture documentation

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Verify health: `docker-compose ps`
3. Review documentation in this repository
4. Contact the development team
