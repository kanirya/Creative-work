#!/bin/bash

# Build script for EduPilot client applications
# This script builds Docker images for the Student Web App and Marketing Site

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}EduPilot Client Apps Docker Build${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Build Student Web App
echo -e "\n${YELLOW}Building Student Web App...${NC}"
docker build -f apps/web/Dockerfile -t edupilot-web:latest . || {
    echo -e "${RED}Failed to build Student Web App${NC}"
    exit 1
}
echo -e "${GREEN}✓ Student Web App built successfully${NC}"

# Build Marketing Site
echo -e "\n${YELLOW}Building Marketing Site...${NC}"
docker build -f apps/marketing/Dockerfile -t edupilot-marketing:latest . || {
    echo -e "${RED}Failed to build Marketing Site${NC}"
    exit 1
}
echo -e "${GREEN}✓ Marketing Site built successfully${NC}"

# Display image sizes
echo -e "\n${YELLOW}Image Sizes:${NC}"
docker images | grep edupilot-web
docker images | grep edupilot-marketing

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Build completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${YELLOW}To run the containers:${NC}"
echo -e "  Student Web App:  docker run -d -p 3000:80 --name web edupilot-web:latest"
echo -e "  Marketing Site:   docker run -d -p 3001:80 --name marketing edupilot-marketing:latest"

echo -e "\n${YELLOW}Or use docker-compose:${NC}"
echo -e "  docker-compose up web marketing"
