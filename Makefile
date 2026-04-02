.PHONY: help start stop restart build logs clean status health dev prod

# Default target
help:
	@echo "EduPilot Docker Compose Management"
	@echo ""
	@echo "Available targets:"
	@echo "  make start       - Start all services"
	@echo "  make stop        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make build       - Build all services"
	@echo "  make logs        - View logs from all services"
	@echo "  make clean       - Stop and remove all containers, networks, and volumes"
	@echo "  make status      - Show status of all services"
	@echo "  make health      - Check health of all services"
	@echo "  make dev         - Start in development mode with hot reload"
	@echo "  make prod        - Start in production mode"
	@echo ""
	@echo "Service-specific targets:"
	@echo "  make start-infra     - Start infrastructure (postgres, redis)"
	@echo "  make start-backend   - Start backend services"
	@echo "  make start-frontend  - Start frontend services"
	@echo "  make logs-api        - View API Gateway logs"
	@echo "  make logs-ai         - View AI Agent logs"
	@echo "  make logs-scraper    - View LMS Scraper logs"
	@echo "  make logs-trans      - View Transcription logs"
	@echo "  make logs-scheduler  - View Scheduler logs"
	@echo "  make logs-web        - View Web App logs"
	@echo "  make logs-marketing  - View Marketing Site logs"
	@echo ""
	@echo "Logging infrastructure targets:"
	@echo "  make logging-start   - Start centralized logging (ELK stack)"
	@echo "  make logging-stop    - Stop centralized logging"
	@echo "  make logging-setup   - Configure Elasticsearch (run after first start)"
	@echo "  make logging-status  - Check logging infrastructure status"
	@echo "  make logging-logs    - View logging infrastructure logs"
	@echo "  make kibana          - Open Kibana in browser"

# Start all services
start:
	@echo "Starting all services..."
	@docker-compose up -d
	@echo "Services started. Run 'make status' to check status."

# Stop all services
stop:
	@echo "Stopping all services..."
	@docker-compose stop
	@echo "Services stopped."

# Restart all services
restart:
	@echo "Restarting all services..."
	@docker-compose restart
	@echo "Services restarted."

# Build all services
build:
	@echo "Building all services..."
	@docker-compose build
	@echo "Build complete."

# Build and start
build-start:
	@echo "Building and starting all services..."
	@docker-compose up -d --build
	@echo "Services built and started."

# View logs
logs:
	@docker-compose logs -f

# Clean everything
clean:
	@echo "WARNING: This will remove all containers, networks, and volumes!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "Cleanup complete."; \
	else \
		echo "Cleanup cancelled."; \
	fi

# Show status
status:
	@docker-compose ps

# Check health
health:
	@echo "Checking service health..."
	@docker-compose ps | grep -E "(healthy|unhealthy|starting)" || echo "No health information available"

# Development mode
dev:
	@echo "Starting in development mode..."
	@docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
	@echo "Development environment started."

# Production mode
prod:
	@echo "Starting in production mode..."
	@docker-compose up -d
	@echo "Production environment started."

# Infrastructure services
start-infra:
	@echo "Starting infrastructure services..."
	@docker-compose up -d postgres redis
	@echo "Infrastructure services started."

# Backend services
start-backend:
	@echo "Starting backend services..."
	@docker-compose up -d api-gateway ai-agent lms-scraper transcription scheduler
	@echo "Backend services started."

# Frontend services
start-frontend:
	@echo "Starting frontend services..."
	@docker-compose up -d web marketing
	@echo "Frontend services started."

# Service-specific logs
logs-api:
	@docker-compose logs -f api-gateway

logs-ai:
	@docker-compose logs -f ai-agent

logs-scraper:
	@docker-compose logs -f lms-scraper

logs-trans:
	@docker-compose logs -f transcription

logs-scheduler:
	@docker-compose logs -f scheduler

logs-web:
	@docker-compose logs -f web

logs-marketing:
	@docker-compose logs -f marketing

logs-postgres:
	@docker-compose logs -f postgres

logs-redis:
	@docker-compose logs -f redis

# Database operations
db-backup:
	@echo "Creating database backup..."
	@docker-compose exec -T postgres pg_dump -U edupilot edupilot > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup created."

db-restore:
	@echo "Restoring database from backup..."
	@read -p "Enter backup file path: " backup_file; \
	docker-compose exec -T postgres psql -U edupilot edupilot < $$backup_file
	@echo "Database restored."

# Restart individual services
restart-api:
	@docker-compose restart api-gateway

restart-ai:
	@docker-compose restart ai-agent

restart-scraper:
	@docker-compose restart lms-scraper

restart-trans:
	@docker-compose restart transcription

restart-scheduler:
	@docker-compose restart scheduler

restart-web:
	@docker-compose restart web

restart-marketing:
	@docker-compose restart marketing

# Shell access
shell-api:
	@docker-compose exec api-gateway bash

shell-ai:
	@docker-compose exec ai-agent bash

shell-scraper:
	@docker-compose exec lms-scraper bash

shell-trans:
	@docker-compose exec transcription bash

shell-scheduler:
	@docker-compose exec scheduler bash

shell-postgres:
	@docker-compose exec postgres psql -U edupilot edupilot

shell-redis:
	@docker-compose exec redis redis-cli

# Validate configuration
validate:
	@echo "Validating docker-compose configuration..."
	@docker-compose config --quiet
	@echo "Configuration is valid."

# Pull latest images
pull:
	@echo "Pulling latest images..."
	@docker-compose pull
	@echo "Images updated."

# Logging infrastructure targets
logging-start:
	@echo "Starting centralized logging infrastructure..."
	@docker-compose -f docker-compose.yml -f logging/docker-compose.logging.yml up -d elasticsearch logstash kibana filebeat
	@echo "Logging infrastructure started."
	@echo "Wait 60 seconds for Elasticsearch to be ready, then run 'make logging-setup'"

logging-stop:
	@echo "Stopping centralized logging infrastructure..."
	@docker-compose -f logging/docker-compose.logging.yml stop elasticsearch logstash kibana filebeat
	@echo "Logging infrastructure stopped."

logging-setup:
	@echo "Configuring Elasticsearch with 30-day retention policy..."
	@bash logging/scripts/setup-elasticsearch.sh || powershell -ExecutionPolicy Bypass -File logging/scripts/setup-elasticsearch.ps1
	@echo "Elasticsearch configured successfully!"
	@echo "Access Kibana at: http://localhost:5601"

logging-status:
	@echo "Logging infrastructure status:"
	@docker-compose -f logging/docker-compose.logging.yml ps

logging-logs:
	@echo "Viewing logging infrastructure logs..."
	@docker-compose -f logging/docker-compose.logging.yml logs -f

logging-logs-elasticsearch:
	@docker-compose -f logging/docker-compose.logging.yml logs -f elasticsearch

logging-logs-logstash:
	@docker-compose -f logging/docker-compose.logging.yml logs -f logstash

logging-logs-kibana:
	@docker-compose -f logging/docker-compose.logging.yml logs -f kibana

logging-logs-filebeat:
	@docker-compose -f logging/docker-compose.logging.yml logs -f filebeat

logging-clean:
	@echo "WARNING: This will remove all logs and logging infrastructure!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $REPLY =~ ^[Yy]$ ]]; then \
		docker-compose -f logging/docker-compose.logging.yml down -v; \
		echo "Logging infrastructure removed."; \
	else \
		echo "Cleanup cancelled."; \
	fi

kibana:
	@echo "Opening Kibana in browser..."
	@command -v xdg-open > /dev/null && xdg-open http://localhost:5601 || \
	 command -v open > /dev/null && open http://localhost:5601 || \
	 echo "Please open http://localhost:5601 in your browser"

# Start everything including logging
start-all:
	@echo "Starting all services including logging infrastructure..."
	@docker-compose -f docker-compose.yml -f logging/docker-compose.logging.yml up -d
	@echo "All services started."
	@echo "Wait 60 seconds, then run 'make logging-setup' to configure Elasticsearch"
