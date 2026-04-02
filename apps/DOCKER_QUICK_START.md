# Docker Quick Start Guide - Client Apps

Quick reference for building and running EduPilot client applications in Docker.

## Build Commands

```bash
# Build both apps
bash scripts/build-client-apps.sh

# Or build individually
docker build -f apps/web/Dockerfile -t edupilot-web:latest .
docker build -f apps/marketing/Dockerfile -t edupilot-marketing:latest .

# Or use docker-compose
docker-compose build web marketing
```

## Run Commands

```bash
# Using docker-compose (recommended)
docker-compose up -d web marketing

# Or run individually
docker run -d -p 3000:80 --name web edupilot-web:latest
docker run -d -p 3001:80 --name marketing edupilot-marketing:latest
```

## Access Applications

- **Student Web App**: http://localhost:3000
- **Marketing Site**: http://localhost:3001

## Health Checks

```bash
# Student Web App
curl http://localhost:3000/api/health

# Marketing Site
curl http://localhost:3001/
```

## View Logs

```bash
docker logs edupilot-web
docker logs edupilot-marketing
```

## Stop Containers

```bash
docker-compose down
# Or
docker stop edupilot-web edupilot-marketing
```

## Environment Variables

### Student Web App
- `NEXT_PUBLIC_API_URL` - API Gateway URL (default: http://localhost:5000)

### Marketing Site
- No environment variables required

## Troubleshooting

```bash
# Check container status
docker ps -a

# Check container health
docker inspect --format='{{.State.Health.Status}}' edupilot-web

# Access container shell
docker exec -it edupilot-web sh

# Rebuild without cache
docker build --no-cache -f apps/web/Dockerfile -t edupilot-web:latest .
```

## Production Deployment

1. Set production environment variables
2. Build images with version tags
3. Push to container registry
4. Deploy using orchestration tool (Kubernetes, ECS, etc.)
5. Configure SSL/TLS at load balancer
6. Set up monitoring and logging

For detailed documentation, see:
- `apps/web/DOCKER_README.md`
- `apps/marketing/DOCKER_README.md`
- `apps/CLIENT_APPS_DOCKER_SUMMARY.md`
