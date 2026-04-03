# EduPilot Desktop App Startup Script

Write-Host "Starting EduPilot Desktop App..." -ForegroundColor Green
Write-Host ""

# Check if backend services are running
Write-Host "Checking backend services..." -ForegroundColor Yellow
$apiGateway = Test-NetConnection -ComputerName localhost -Port 5000 -WarningAction SilentlyContinue -InformationLevel Quiet

if (-not $apiGateway) {
    Write-Host "WARNING: Backend services are not running!" -ForegroundColor Red
    Write-Host "Please start Docker services first:" -ForegroundColor Yellow
    Write-Host "  docker-compose up -d" -ForegroundColor Cyan
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit
    }
}

Write-Host "Backend services are running" -ForegroundColor Green
Write-Host ""

# Stop web container to free port 3000
Write-Host "Stopping web container to free port 3000..." -ForegroundColor Yellow
docker-compose stop web 2>$null

Write-Host ""
Write-Host "Starting desktop app..." -ForegroundColor Green
Write-Host "The Electron window will open shortly..." -ForegroundColor Cyan
Write-Host ""

# Start the desktop app
Set-Location $PSScriptRoot
pnpm dev
