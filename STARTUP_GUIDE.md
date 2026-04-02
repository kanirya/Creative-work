# EduPilot Startup Guide

## ⚠️ IMPORTANT: Before You Start

### Required Configuration

1. **OpenAI API Key** (REQUIRED)
   - Edit `.env` file
   - Replace `OPENAI_API_KEY=sk-your-openai-api-key-here` with your actual OpenAI API key
   - Without this, the AI Agent service will not work

2. **Docker Requirements**
   - Docker Desktop must be running
   - At least 8GB RAM available
   - At least 20GB disk space

## Quick Start (3 Steps)

### Step 1: Configure Environment

```bash
# Edit .env file and add your OpenAI API key
notepad .env  # Windows
# or
nano .env     # Linux/Mac
```

### Step 2: Start Core Services

```powershell
# Windows PowerShell
docker-compose up -d postgres redis

# Wait for database to be ready (about 30 seconds)
Start-Sleep -Seconds 30

# Start backend services
docker-compose up -d api-gateway ai-agent lms-scraper transcription scheduler
```

### Step 3: Start Client Apps (Optional)

```powershell
# Build and start web apps
docker-compose up -d web marketing
```

## Access Points

Once services are running:

- **Web App**: http://localhost:3000
- **Marketing Site**: http://localhost:3001  
- **API Gateway**: http://localhost:5000
- **API Documentation**: http://localhost:5000/swagger
- **AI Agent**: http://localhost:8001
- **LMS Scraper**: http://localhost:8002
- **Transcription**: http://localhost:8003
- **Scheduler**: http://localhost:8004

## Check Service Status

```powershell
# View all services
docker-compose ps

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api-gateway
```

## Troubleshooting

### Services Won't Start

1. Check Docker is running:
   ```powershell
   docker ps
   ```

2. Check logs for errors:
   ```powershell
   docker-compose logs
   ```

3. Restart services:
   ```powershell
   docker-compose restart
   ```

### Database Connection Errors

```powershell
# Check postgres is healthy
docker-compose ps postgres

# Test database connection
docker-compose exec postgres psql -U edupilot -d edupilot -c "SELECT 1"
```

### Port Already in Use

If you see "port already allocated" errors:

1. Check what's using the port:
   ```powershell
   netstat -ano | findstr :5000
   ```

2. Stop the conflicting service or change the port in `docker-compose.yml`

### Out of Memory

1. Open Docker Desktop
2. Go to Settings → Resources
3. Increase Memory to at least 8GB
4. Click "Apply & Restart"

## Stop Services

```powershell
# Stop all services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove everything including data (WARNING!)
docker-compose down -v
```

## Development Mode

For development with hot reload:

```powershell
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

## Minimal Setup (Testing Only)

If you just want to test the API without client apps:

```powershell
# Start only backend
docker-compose up -d postgres redis api-gateway ai-agent

# Check health
curl http://localhost:5000/health
```

## Next Steps

1. **Initialize Database**: The database schema is automatically applied on first startup
2. **Create Test User**: Use the API to register a test student
3. **Test API**: Visit http://localhost:5000/swagger to explore the API
4. **Access Web App**: Open http://localhost:3000 to use the student interface

## Common Commands

```powershell
# View all running containers
docker ps

# View logs for all services
docker-compose logs -f

# Restart a specific service
docker-compose restart api-gateway

# Rebuild a service
docker-compose build api-gateway
docker-compose up -d api-gateway

# Execute command in container
docker-compose exec api-gateway bash

# View resource usage
docker stats
```

## Production Deployment

For production deployment, see:
- [DOCKER_README.md](./DOCKER_README.md) - Complete Docker guide
- [nginx/DEPLOYMENT.md](./nginx/DEPLOYMENT.md) - Nginx reverse proxy setup
- [logging/DEPLOYMENT.md](./logging/DEPLOYMENT.md) - Logging infrastructure
- [monitoring/DEPLOYMENT.md](./monitoring/DEPLOYMENT.md) - Monitoring setup

## Support

If you encounter issues:
1. Check the logs: `docker-compose logs -f`
2. Verify all services are healthy: `docker-compose ps`
3. Review the [DOCKER_README.md](./DOCKER_README.md) for detailed troubleshooting
