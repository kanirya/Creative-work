#!/bin/bash

# EduPilot Docker Compose Startup Script
# This script starts all services in the correct order with health checks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
MAX_WAIT=300  # Maximum wait time in seconds

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check .env file
    if [ ! -f "$ENV_FILE" ]; then
        print_warn ".env file not found. Creating from .env.example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_warn "Please update .env with your actual configuration values."
            exit 1
        else
            print_error ".env.example not found. Cannot create .env file."
            exit 1
        fi
    fi
    
    print_info "Prerequisites check passed."
}

wait_for_service() {
    local service=$1
    local max_attempts=$((MAX_WAIT / 5))
    local attempt=0
    
    print_info "Waiting for $service to be healthy..."
    
    while [ $attempt -lt $max_attempts ]; do
        health_status=$(docker-compose ps -q $service | xargs docker inspect --format='{{.State.Health.Status}}' 2>/dev/null || echo "starting")
        
        if [ "$health_status" = "healthy" ]; then
            print_info "$service is healthy!"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 5
    done
    
    print_error "$service failed to become healthy within $MAX_WAIT seconds"
    return 1
}

start_infrastructure() {
    print_info "Starting infrastructure services (postgres, redis)..."
    docker-compose up -d postgres redis
    
    wait_for_service postgres
    wait_for_service redis
}

start_backend() {
    print_info "Starting backend services..."
    
    # Start API Gateway first
    print_info "Starting API Gateway..."
    docker-compose up -d api-gateway
    wait_for_service api-gateway
    
    # Start microservices in parallel
    print_info "Starting microservices (ai-agent, lms-scraper, transcription)..."
    docker-compose up -d ai-agent lms-scraper transcription
    
    wait_for_service ai-agent
    wait_for_service lms-scraper
    wait_for_service transcription
    
    # Start scheduler last
    print_info "Starting scheduler..."
    docker-compose up -d scheduler
    wait_for_service scheduler
}

start_frontend() {
    print_info "Starting frontend services..."
    docker-compose up -d web marketing
    
    wait_for_service web
    wait_for_service marketing
}

show_status() {
    print_info "Service Status:"
    docker-compose ps
    
    echo ""
    print_info "Access URLs:"
    echo "  - Web App:        http://localhost:3000"
    echo "  - Marketing Site: http://localhost:3001"
    echo "  - API Gateway:    http://localhost:5000"
    echo "  - AI Agent:       http://localhost:8001"
    echo "  - LMS Scraper:    http://localhost:8002"
    echo "  - Transcription:  http://localhost:8003"
    echo "  - Scheduler:      http://localhost:8004"
    echo "  - PostgreSQL:     localhost:5432"
    echo "  - Redis:          localhost:6379"
}

# Main execution
main() {
    print_info "Starting EduPilot Full-Stack System..."
    echo ""
    
    check_prerequisites
    
    # Start services in order
    start_infrastructure
    start_backend
    start_frontend
    
    echo ""
    print_info "All services started successfully!"
    echo ""
    
    show_status
    
    echo ""
    print_info "To view logs: docker-compose logs -f"
    print_info "To stop services: docker-compose stop"
    print_info "To stop and remove: docker-compose down"
}

# Run main function
main
