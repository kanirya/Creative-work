# Docker Compose Configuration Guide

## Overview

This docker-compose.yml orchestrates the complete EduPilot full-stack system with 9 services:
- 2 infrastructure services (PostgreSQL, Redis)
- 5 backend services (API Gateway, AI Agent, LMS Scraper, Transcription, Scheduler)
- 2 frontend services (Web App, Marketing Site)

## Architecture

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
│  │          │   │(8002)    │   │          │   │          ││
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

## Services Configuration

### Infrastructure Services

#### PostgreSQL (postgres)
- **Image**: pgvector/pgvector:pg16
- **Port**: 5432
- **Volume**: postgres-data (persistent storage)
- **Health Check**: pg_isready command every 10s
- **Purpose**: Primary database with vector search capabilities
- **Dependencies**: None (base service)

#### Redis (redis)
- **Image**: redis:7-alpine
- **Port**: 6379
- **Volume**: redis-data (persistent storage with AOF)
- **Health Check**: redis-cli ping every 10s
- **Purpose**: Caching and session management
- **Dependencies**: None (base service)

### Backend Services

#### API Gateway (api-gateway)
- **Technology**: .NET 8 Web API
- **Port**: 5000 → 8080 (internal)
- **Health Check**: /health endpoint every 30s
- **Dependencies**: postgres (healthy), redis (healthy)
- **Purpose**: Main backend entry point, routes requests to microservices
- **Key Environment Variables**:
  - ConnectionStrings__DefaultConnection
  - ConnectionStrings__Redis
  - JwtSettings__*
  - ServiceUrls__* (all microservice URLs)

#### AI Agent (ai-agent)
- **Technology**: Python FastAPI + LangChain
- **Port**: 8001
- **Health Check**: /health endpoint every 30s
- **Dependencies**: postgres (healthy), redis (healthy)
- **Purpose**: Natural language processing and RAG
- **Key Environment Variables**:
  - OPENAI_API_KEY
  - OPENAI_MODEL
  - OPENAI_EMBEDDING_MODEL

#### LMS Scraper (lms-scraper)
- **Technology**: Python FastAPI + Playwright
- **Port**: 8002
- **Health Check**: /health endpoint every 30s
- **Dependencies**: postgres (healthy), api-gateway (healthy)
- **Purpose**: Extract data from university LMS
- **Key Environment Variables**:
  - DATABASE_URL
  - API_GATEWAY_URL

#### Transcription (transcription)
- **Technology**: Python FastAPI + Whisper
- **Port**: 8003
- **Health Check**: /health endpoint every 30s
- **Dependencies**: postgres (healthy), api-gateway (healthy)
- **Purpose**: Transcribe lecture recordings
- **Key Environment Variables**:
  - OPENAI_API_KEY
  - AWS_* (for S3 storage)

#### Scheduler (scheduler)
- **Technology**: Python FastAPI + APScheduler
- **Port**: 8004
- **Health Check**: /health endpoint every 30s
- **Dependencies**: postgres (healthy), api-gateway (healthy), lms-scraper (healthy), transcription (healthy)
- **Purpose**: Automated task scheduling and execution
- **Key Environment Variables**:
  - SCRAPER_SERVICE_URL
  - TRANSCRIPTION_SERVICE_URL
  - AI_AGENT_SERVICE_URL

### Frontend Services

#### Web App (web)
- **Technology**: Next.js 14 + nginx
- **Port**: 3000 → 80 (internal)
- **Health Check**: /api/health endpoint every 30s
- **Dependencies**: api-gateway (healthy)
- **Purpose**: Student web application
- **Key Environment Variables**:
  - NEXT_PUBLIC_API_URL
  - NEXT_PUBLIC_WEB_APP_URL

#### Marketing Site (marketing)
- **Technology**: Next.js 14 + nginx
- **Port**: 3001 → 80 (internal)
- **Health Check**: / endpoint every 30s
- **Dependencies**: None
- **Purpose**: Public marketing website
- **Key Environment Variables**:
  - NEXT_PUBLIC_API_URL
  - NEXT_PUBLIC_MARKETING_URL

## Service Dependencies

```
postgres ─┬─> api-gateway ─┬─> web
          │                 │
          │                 ├─> lms-scraper ─┐
          │                 │                 │
          │                 ├─> transcription ├─> scheduler
          │                 │                 │
          │                 └─> ai-agent ─────┘
          │
redis ────┤
          │
          └─> (all backend services)

marketing (independent)
```

## Health Checks

All services implement health checks with the following configuration:

| Service       | Endpoint/Command              | Interval | Timeout | Retries | Start Period |
|---------------|-------------------------------|----------|---------|---------|--------------|
| postgres      | pg_isready                    | 10s      | 5s      | 5       | 10s          |
| redis         | redis-cli ping                | 10s      | 5s      | 5       | 5s           |
| api-gateway   | curl /health                  | 30s      | 10s     | 3       | 40s          |
| ai-agent      | curl /health                  | 30s      | 10s     | 3       | 30s          |
| lms-scraper   | curl /health                  | 30s      | 10s     | 3       | 30s          |
| transcription | curl /health                  | 30s      | 10s     | 3       | 30s          |
| scheduler     | curl /health                  | 30s      | 10s     | 3       | 30s          |
| web           | wget /api/health              | 30s      | 10s     | 3       | 40s          |
| marketing     | wget /                        | 30s      | 10s     | 3       | 40s          |

## Environment Variables

### Required Variables

Create a `.env` file in the root directory with these required variables:

```bash
# Database
DATABASE_URL=postgresql://edupilot:password@postgres:5432/edupilot
POSTGRES_DB=edupilot
POSTGRES_USER=edupilot
POSTGRES_PASSWORD=your_secure_password

# Redis
REDIS_URL=redis://redis:6379

# JWT
JWT_SECRET_KEY=your_256_bit_secret_key_here
JWT_ISSUER=EduPilot
JWT_AUDIENCE=EduPilot

# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Optional Variables

```bash
# AWS S3 (for transcription storage)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=ap-south-1
AWS_S3_BUCKET=edupilot-storage

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# URLs
API_URL=http://localhost:5000
WEB_APP_URL=http://localhost:3000
MARKETING_URL=http://localhost:3001
```

## Networking

All services communicate through the `edupilot-network` bridge network:

- **Internal DNS**: Services can reach each other using service names (e.g., `http://api-gateway:8080`)
- **External Access**: Only exposed ports are accessible from host machine
- **Isolation**: Network is isolated from other Docker networks

## Volume Management

### Persistent Volumes

1. **postgres-data**: Stores PostgreSQL database files
   - Location: Docker managed volume
   - Backup: Use `docker-compose exec postgres pg_dump`

2. **redis-data**: Stores Redis data with AOF persistence
   - Location: Docker managed volume
   - Backup: Automatic via AOF (Append-Only File)

### Volume Commands

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect edupilot_postgres-data

# Backup postgres volume
docker-compose exec postgres pg_dump -U edupilot edupilot > backup.sql

# Restore postgres volume
docker-compose exec -T postgres psql -U edupilot edupilot < backup.sql

# Remove volumes (WARNING: deletes all data)
docker-compose down -v
```

## Usage

### Starting Services

```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d postgres redis api-gateway

# Start with build
docker-compose up -d --build

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f api-gateway
```

### Stopping Services

```bash
# Stop all services
docker-compose stop

# Stop specific service
docker-compose stop api-gateway

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes
docker-compose down -v
```

### Service Management

```bash
# Restart service
docker-compose restart api-gateway

# Rebuild service
docker-compose build api-gateway

# Scale service (if supported)
docker-compose up -d --scale ai-agent=3

# View service status
docker-compose ps

# Execute command in service
docker-compose exec api-gateway bash
```

### Health Monitoring

```bash
# Check health status
docker-compose ps

# View health check logs
docker inspect --format='{{json .State.Health}}' edupilot-api-gateway | jq

# Monitor all services
watch -n 2 'docker-compose ps'
```

## Startup Sequence

The services start in this order based on dependencies:

1. **postgres** and **redis** (parallel, no dependencies)
2. **api-gateway** (waits for postgres and redis to be healthy)
3. **ai-agent** (waits for postgres and redis to be healthy)
4. **lms-scraper** and **transcription** (wait for postgres and api-gateway to be healthy)
5. **scheduler** (waits for postgres, api-gateway, lms-scraper, and transcription to be healthy)
6. **web** (waits for api-gateway to be healthy)
7. **marketing** (no dependencies, starts immediately)

Total startup time: ~2-3 minutes for all services to be healthy

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs service-name

# Check health status
docker-compose ps

# Restart service
docker-compose restart service-name

# Rebuild and restart
docker-compose up -d --build service-name
```

### Database Connection Issues

```bash
# Check postgres is healthy
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U edupilot -d edupilot -c "SELECT 1"

# Check environment variables
docker-compose exec api-gateway env | grep DATABASE
```

### Network Issues

```bash
# Inspect network
docker network inspect edupilot_edupilot-network

# Test connectivity between services
docker-compose exec api-gateway curl http://ai-agent:8001/health
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Check service logs for errors
docker-compose logs --tail=100 service-name

# Restart problematic service
docker-compose restart service-name
```

## Production Considerations

### Security

1. **Environment Variables**: Use Docker secrets or external secret management
2. **Network Isolation**: Use separate networks for frontend/backend
3. **TLS/SSL**: Add nginx reverse proxy with SSL certificates
4. **Firewall**: Restrict exposed ports

### Scaling

1. **Horizontal Scaling**: Scale stateless services (api-gateway, ai-agent)
2. **Load Balancing**: Add nginx or HAProxy for load distribution
3. **Database**: Consider read replicas for PostgreSQL
4. **Caching**: Use Redis Cluster for high availability

### Monitoring

1. **Logging**: Integrate with ELK stack or Loki
2. **Metrics**: Add Prometheus and Grafana
3. **Tracing**: Implement distributed tracing with Jaeger
4. **Alerts**: Configure alerting for health check failures

### Backup Strategy

1. **Database**: Automated daily backups with retention policy
2. **Volumes**: Regular volume snapshots
3. **Configuration**: Version control for docker-compose.yml
4. **Disaster Recovery**: Document recovery procedures

## Validation

Requirement 14.1 is satisfied through:

✅ **Service Configuration**: All 9 services properly configured
✅ **Dependencies**: Proper dependency chains with health checks
✅ **Health Checks**: All services have appropriate health checks
✅ **Environment Variables**: Comprehensive environment configuration
✅ **Networking**: Isolated bridge network for service communication
✅ **Volumes**: Persistent storage for postgres and redis
✅ **Restart Policies**: All services use `unless-stopped` policy
✅ **Resource Management**: Proper service isolation and management
