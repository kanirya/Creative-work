# EduPilot Docker Compose Startup Script (PowerShell)
# This script starts all services in the correct order with health checks

param(
    [switch]$Dev,
    [switch]$Build
)

# Configuration
$ComposeFile = "docker-compose.yml"
$DevComposeFile = "docker-compose.dev.yml"
$EnvFile = ".env"
$MaxWait = 300  # Maximum wait time in seconds

# Functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check Docker
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker is not installed. Please install Docker Desktop first."
        exit 1
    }
    
    # Check Docker Compose
    if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Write-Error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    }
    
    # Check .env file
    if (-not (Test-Path $EnvFile)) {
        Write-Warn ".env file not found."
        if (Test-Path ".env.example") {
            Write-Warn "Creating .env from .env.example..."
            Copy-Item ".env.example" $EnvFile
            Write-Warn "Please update .env with your actual configuration values."
            exit 1
        } else {
            Write-Error ".env.example not found. Cannot create .env file."
            exit 1
        }
    }
    
    Write-Info "Prerequisites check passed."
}

function Wait-ForService {
    param(
        [string]$ServiceName,
        [int]$MaxAttempts = ($MaxWait / 5)
    )
    
    Write-Info "Waiting for $ServiceName to be healthy..."
    
    $attempt = 0
    while ($attempt -lt $MaxAttempts) {
        try {
            $containerId = docker-compose ps -q $ServiceName 2>$null
            if ($containerId) {
                $healthStatus = docker inspect --format='{{.State.Health.Status}}' $containerId 2>$null
                
                if ($healthStatus -eq "healthy") {
                    Write-Info "$ServiceName is healthy!"
                    return $true
                }
            }
        } catch {
            # Service not ready yet
        }
        
        $attempt++
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 5
    }
    
    Write-Host ""
    Write-Error "$ServiceName failed to become healthy within $MaxWait seconds"
    return $false
}

function Start-Infrastructure {
    Write-Info "Starting infrastructure services (postgres, redis)..."
    
    if ($Build) {
        docker-compose up -d --build postgres redis
    } else {
        docker-compose up -d postgres redis
    }
    
    if (-not (Wait-ForService "postgres")) { exit 1 }
    if (-not (Wait-ForService "redis")) { exit 1 }
}

function Start-Backend {
    Write-Info "Starting backend services..."
    
    # Start API Gateway first
    Write-Info "Starting API Gateway..."
    if ($Build) {
        docker-compose up -d --build api-gateway
    } else {
        docker-compose up -d api-gateway
    }
    if (-not (Wait-ForService "api-gateway")) { exit 1 }
    
    # Start microservices in parallel
    Write-Info "Starting microservices (ai-agent, lms-scraper, transcription)..."
    if ($Build) {
        docker-compose up -d --build ai-agent lms-scraper transcription
    } else {
        docker-compose up -d ai-agent lms-scraper transcription
    }
    
    if (-not (Wait-ForService "ai-agent")) { exit 1 }
    if (-not (Wait-ForService "lms-scraper")) { exit 1 }
    if (-not (Wait-ForService "transcription")) { exit 1 }
    
    # Start scheduler last
    Write-Info "Starting scheduler..."
    if ($Build) {
        docker-compose up -d --build scheduler
    } else {
        docker-compose up -d scheduler
    }
    if (-not (Wait-ForService "scheduler")) { exit 1 }
}

function Start-Frontend {
    Write-Info "Starting frontend services..."
    
    if ($Build) {
        docker-compose up -d --build web marketing
    } else {
        docker-compose up -d web marketing
    }
    
    if (-not (Wait-ForService "web")) { exit 1 }
    if (-not (Wait-ForService "marketing")) { exit 1 }
}

function Show-Status {
    Write-Info "Service Status:"
    docker-compose ps
    
    Write-Host ""
    Write-Info "Access URLs:"
    Write-Host "  - Web App:        http://localhost:3000" -ForegroundColor Cyan
    Write-Host "  - Marketing Site: http://localhost:3001" -ForegroundColor Cyan
    Write-Host "  - API Gateway:    http://localhost:5000" -ForegroundColor Cyan
    Write-Host "  - AI Agent:       http://localhost:8001" -ForegroundColor Cyan
    Write-Host "  - LMS Scraper:    http://localhost:8002" -ForegroundColor Cyan
    Write-Host "  - Transcription:  http://localhost:8003" -ForegroundColor Cyan
    Write-Host "  - Scheduler:      http://localhost:8004" -ForegroundColor Cyan
    Write-Host "  - PostgreSQL:     localhost:5432" -ForegroundColor Cyan
    Write-Host "  - Redis:          localhost:6379" -ForegroundColor Cyan
}

# Main execution
function Main {
    Write-Info "Starting EduPilot Full-Stack System..."
    Write-Host ""
    
    Test-Prerequisites
    
    # Set compose file based on mode
    if ($Dev) {
        Write-Info "Starting in DEVELOPMENT mode..."
        $env:COMPOSE_FILE = "$ComposeFile;$DevComposeFile"
    }
    
    # Start services in order
    Start-Infrastructure
    Start-Backend
    Start-Frontend
    
    Write-Host ""
    Write-Info "All services started successfully!"
    Write-Host ""
    
    Show-Status
    
    Write-Host ""
    Write-Info "To view logs: docker-compose logs -f"
    Write-Info "To stop services: docker-compose stop"
    Write-Info "To stop and remove: docker-compose down"
}

# Run main function
Main
