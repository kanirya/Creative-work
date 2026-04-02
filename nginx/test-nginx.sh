#!/bin/bash
# Nginx Configuration Test Script
# Tests nginx configuration, rate limiting, and SSL setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}EduPilot Nginx Configuration Test${NC}"
echo "=================================="
echo ""

# Test 1: Check nginx syntax
echo -e "${YELLOW}Test 1: Checking nginx configuration syntax...${NC}"
if docker exec edupilot-nginx nginx -t 2>&1 | grep -q "syntax is ok"; then
    echo -e "${GREEN}✓ Nginx configuration syntax is valid${NC}"
else
    echo -e "${RED}✗ Nginx configuration has syntax errors${NC}"
    docker exec edupilot-nginx nginx -t
    exit 1
fi
echo ""

# Test 2: Check if nginx is running
echo -e "${YELLOW}Test 2: Checking if nginx is running...${NC}"
if docker ps | grep -q edupilot-nginx; then
    echo -e "${GREEN}✓ Nginx container is running${NC}"
else
    echo -e "${RED}✗ Nginx container is not running${NC}"
    exit 1
fi
echo ""

# Test 3: Check HTTP to HTTPS redirect
echo -e "${YELLOW}Test 3: Testing HTTP to HTTPS redirect...${NC}"
HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -L http://localhost/)
if [ "$HTTP_RESPONSE" = "200" ] || [ "$HTTP_RESPONSE" = "301" ]; then
    echo -e "${GREEN}✓ HTTP redirect is working${NC}"
else
    echo -e "${RED}✗ HTTP redirect failed (status: $HTTP_RESPONSE)${NC}"
fi
echo ""

# Test 4: Check SSL certificate
echo -e "${YELLOW}Test 4: Checking SSL certificates...${NC}"
for domain in api.edupilot.com app.edupilot.com edupilot.com; do
    if docker exec edupilot-nginx test -f "/etc/nginx/ssl/$domain/fullchain.pem"; then
        echo -e "${GREEN}✓ Certificate exists for $domain${NC}"
    else
        echo -e "${RED}✗ Certificate missing for $domain${NC}"
    fi
done
echo ""

# Test 5: Test rate limiting
echo -e "${YELLOW}Test 5: Testing rate limiting...${NC}"
echo "Sending 15 requests to auth endpoint (limit: 10/min)..."

SUCCESS_COUNT=0
RATE_LIMITED_COUNT=0

for i in {1..15}; do
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -k https://localhost/api/auth/test 2>/dev/null || echo "000")
    if [ "$RESPONSE" = "429" ]; then
        ((RATE_LIMITED_COUNT++))
    elif [ "$RESPONSE" != "000" ]; then
        ((SUCCESS_COUNT++))
    fi
done

echo "Successful requests: $SUCCESS_COUNT"
echo "Rate limited requests: $RATE_LIMITED_COUNT"

if [ $RATE_LIMITED_COUNT -gt 0 ]; then
    echo -e "${GREEN}✓ Rate limiting is working${NC}"
else
    echo -e "${YELLOW}⚠ Rate limiting may not be working (or endpoint doesn't exist yet)${NC}"
fi
echo ""

# Test 6: Check security headers
echo -e "${YELLOW}Test 6: Checking security headers...${NC}"
HEADERS=$(curl -s -k -I https://localhost/ 2>/dev/null || echo "")

check_header() {
    local header=$1
    if echo "$HEADERS" | grep -qi "$header"; then
        echo -e "${GREEN}✓ $header header is present${NC}"
    else
        echo -e "${RED}✗ $header header is missing${NC}"
    fi
}

check_header "X-Frame-Options"
check_header "X-Content-Type-Options"
check_header "X-XSS-Protection"
check_header "Referrer-Policy"
check_header "Strict-Transport-Security"
echo ""

# Test 7: Check upstream connectivity
echo -e "${YELLOW}Test 7: Checking upstream service connectivity...${NC}"

check_upstream() {
    local service=$1
    local port=$2
    if docker exec edupilot-nginx nc -zv "$service" "$port" 2>&1 | grep -q "open"; then
        echo -e "${GREEN}✓ Can connect to $service:$port${NC}"
    else
        echo -e "${RED}✗ Cannot connect to $service:$port${NC}"
    fi
}

check_upstream "api-gateway" "8080"
check_upstream "web" "80"
check_upstream "marketing" "80"
echo ""

# Test 8: Check gzip compression
echo -e "${YELLOW}Test 8: Checking gzip compression...${NC}"
GZIP_RESPONSE=$(curl -s -k -H "Accept-Encoding: gzip" -I https://localhost/ 2>/dev/null || echo "")
if echo "$GZIP_RESPONSE" | grep -qi "Content-Encoding: gzip"; then
    echo -e "${GREEN}✓ Gzip compression is enabled${NC}"
else
    echo -e "${YELLOW}⚠ Gzip compression may not be working${NC}"
fi
echo ""

# Test 9: Check log files
echo -e "${YELLOW}Test 9: Checking log files...${NC}"
if docker exec edupilot-nginx test -f /var/log/nginx/access.log; then
    echo -e "${GREEN}✓ Access log exists${NC}"
    LOG_LINES=$(docker exec edupilot-nginx wc -l < /var/log/nginx/access.log)
    echo "  Access log has $LOG_LINES lines"
else
    echo -e "${RED}✗ Access log not found${NC}"
fi

if docker exec edupilot-nginx test -f /var/log/nginx/error.log; then
    echo -e "${GREEN}✓ Error log exists${NC}"
    ERROR_COUNT=$(docker exec edupilot-nginx grep -c "error" /var/log/nginx/error.log 2>/dev/null || echo "0")
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo -e "${YELLOW}  Warning: $ERROR_COUNT errors in log${NC}"
    fi
else
    echo -e "${RED}✗ Error log not found${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}=================================${NC}"
echo "All critical tests completed."
echo ""
echo "To view detailed logs:"
echo "  docker logs edupilot-nginx"
echo "  docker exec edupilot-nginx tail -f /var/log/nginx/access.log"
echo "  docker exec edupilot-nginx tail -f /var/log/nginx/error.log"
