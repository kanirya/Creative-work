#!/bin/bash

set -e

echo "🚀 EduPilot Development Environment Setup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}✗ $1 is not installed${NC}"
        echo "  Please install $1 and try again"
        exit 1
    else
        echo -e "${GREEN}✓ $1 is installed${NC}"
    fi
}

check_command node
check_command npm
check_command docker
check_command python3

# Check Node version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    echo -e "${RED}✗ Node.js version must be 20 or higher${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js version is $NODE_VERSION${NC}"

# Check .NET SDK
if command -v dotnet &> /dev/null; then
    echo -e "${GREEN}✓ .NET SDK is installed${NC}"
else
    echo -e "${YELLOW}⚠ .NET SDK not found. Install .NET 8 SDK from https://dotnet.microsoft.com/download${NC}"
fi

# Copy environment file
echo -e "\n${YELLOW}Setting up environment variables...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file from .env.example${NC}"
    echo -e "${YELLOW}⚠ Please edit .env with your configuration${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Install Node dependencies
echo -e "\n${YELLOW}Installing Node.js dependencies...${NC}"
npm install
echo -e "${GREEN}✓ Node.js dependencies installed${NC}"

# Install Python dependencies for microservices
echo -e "\n${YELLOW}Installing Python dependencies...${NC}"

install_python_deps() {
    if [ -d "$1" ] && [ -f "$1/requirements.txt" ]; then
        echo "  Installing dependencies for $1..."
        cd "$1"
        python3 -m pip install -r requirements.txt --quiet
        cd - > /dev/null
        echo -e "${GREEN}  ✓ $1 dependencies installed${NC}"
    fi
}

install_python_deps "services/ai-agent"
install_python_deps "services/lms-scraper"
install_python_deps "services/transcription"
install_python_deps "services/scheduler"

# Install Playwright browsers
echo -e "\n${YELLOW}Installing Playwright browsers...${NC}"
if [ -d "services/lms-scraper" ]; then
    cd services/lms-scraper
    python3 -m playwright install chromium
    cd - > /dev/null
    echo -e "${GREEN}✓ Playwright browsers installed${NC}"
fi

# Start Docker services
echo -e "\n${YELLOW}Starting Docker services (PostgreSQL and Redis)...${NC}"
docker-compose up -d postgres redis

# Wait for PostgreSQL to be ready
echo -e "\n${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
until docker-compose exec -T postgres pg_isready -U edupilot > /dev/null 2>&1; do
    echo "  Waiting for PostgreSQL..."
    sleep 2
done
echo -e "${GREEN}✓ PostgreSQL is ready${NC}"

# Run database migrations (if .NET project exists)
if [ -d "services/api-gateway" ]; then
    echo -e "\n${YELLOW}Running database migrations...${NC}"
    cd services/api-gateway
    if command -v dotnet &> /dev/null; then
        dotnet ef database update || echo -e "${YELLOW}⚠ Migrations will be run when API Gateway starts${NC}"
    fi
    cd - > /dev/null
fi

# Print success message
echo -e "\n${GREEN}=========================================="
echo "✓ Setup completed successfully!"
echo "==========================================${NC}"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Edit .env file with your API keys and configuration"
echo "2. Start all services: docker-compose up -d"
echo "3. Start development: npm run dev"
echo ""
echo "Service URLs:"
echo "  - Web App: http://localhost:3000"
echo "  - Marketing: http://localhost:3001"
echo "  - API Gateway: http://localhost:5000"
echo "  - API Docs: http://localhost:5000/swagger"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo -e "${GREEN}Happy coding! 🎉${NC}"
