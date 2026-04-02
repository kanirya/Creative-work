#!/bin/bash

# Script to validate all Dockerfiles in the EduPilot project
# This script checks for the existence and basic syntax of Dockerfiles

set -e

echo "🔍 Validating EduPilot Dockerfiles..."
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counter for validation
TOTAL=0
PASSED=0
FAILED=0

# Function to validate a Dockerfile
validate_dockerfile() {
    local service=$1
    local dockerfile_path=$2
    
    TOTAL=$((TOTAL + 1))
    
    echo -n "Checking $service... "
    
    if [ ! -f "$dockerfile_path" ]; then
        echo -e "${RED}✗ FAILED${NC} - Dockerfile not found"
        FAILED=$((FAILED + 1))
        return 1
    fi
    
    # Check if Dockerfile has FROM instruction
    if ! grep -q "^FROM" "$dockerfile_path"; then
        echo -e "${RED}✗ FAILED${NC} - No FROM instruction"
        FAILED=$((FAILED + 1))
        return 1
    fi
    
    # Check if Dockerfile has WORKDIR
    if ! grep -q "^WORKDIR" "$dockerfile_path"; then
        echo -e "${YELLOW}⚠ WARNING${NC} - No WORKDIR instruction"
    fi
    
    # Check if Dockerfile has EXPOSE
    if ! grep -q "^EXPOSE" "$dockerfile_path"; then
        echo -e "${YELLOW}⚠ WARNING${NC} - No EXPOSE instruction"
    fi
    
    # Check if Dockerfile has HEALTHCHECK
    if ! grep -q "^HEALTHCHECK" "$dockerfile_path"; then
        echo -e "${YELLOW}⚠ WARNING${NC} - No HEALTHCHECK instruction"
    fi
    
    # Check if .dockerignore exists
    local dockerignore_path=$(dirname "$dockerfile_path")/.dockerignore
    if [ ! -f "$dockerignore_path" ]; then
        echo -e "${YELLOW}⚠ WARNING${NC} - No .dockerignore file"
    fi
    
    echo -e "${GREEN}✓ PASSED${NC}"
    PASSED=$((PASSED + 1))
    return 0
}

# Validate all services
echo "=== Backend Services ==="
echo ""

validate_dockerfile "API Gateway (.NET 8)" "services/api-gateway/Dockerfile"
validate_dockerfile "AI Agent Service" "services/ai-agent/Dockerfile"
validate_dockerfile "LMS Scraper Service" "services/lms-scraper/Dockerfile"
validate_dockerfile "Transcription Service" "services/transcription/Dockerfile"
validate_dockerfile "Scheduler Service" "services/scheduler/Dockerfile"

echo ""
echo "=== Validation Summary ==="
echo -e "Total: $TOTAL"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All Dockerfiles validated successfully!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some Dockerfiles failed validation${NC}"
    exit 1
fi
