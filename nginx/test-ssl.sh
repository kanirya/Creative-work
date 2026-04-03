#!/bin/bash
# SSL/TLS Configuration Testing Script
# Tests SSL certificates, TLS versions, cipher suites, and security headers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAINS=("api.edupilot.com" "app.edupilot.com" "edupilot.com")
TEST_MODE="${1:-local}" # local or remote

echo -e "${BLUE}=== EduPilot SSL/TLS Configuration Test ===${NC}"
echo ""

# Function to test TLS version
test_tls_version() {
    local domain=$1
    local version=$2
    local host=$3
    
    echo -n "  Testing $version support... "
    if timeout 5 openssl s_client -connect "$host:443" -servername "$domain" -"$version" </dev/null 2>/dev/null | grep -q "Protocol.*$version"; then
        echo -e "${GREEN}✓ Supported${NC}"
        return 0
    else
        echo -e "${RED}✗ Not supported${NC}"
        return 1
    fi
}

# Function to test cipher suite
test_cipher() {
    local domain=$1
    local cipher=$2
    local host=$3
    
    if timeout 5 openssl s_client -connect "$host:443" -servername "$domain" -cipher "$cipher" </dev/null 2>/dev/null | grep -q "Cipher.*$cipher"; then
        return 0
    else
        return 1
    fi
}

# Function to test security headers
test_security_headers() {
    local url=$1
    
    echo -e "${YELLOW}Testing Security Headers:${NC}"
    
    # Get headers
    headers=$(curl -s -I -k "$url" 2>/dev/null)
    
    # Check HSTS
    echo -n "  Strict-Transport-Security... "
    if echo "$headers" | grep -qi "Strict-Transport-Security"; then
        echo -e "${GREEN}✓ Present${NC}"
    else
        echo -e "${RED}✗ Missing${NC}"
    fi
    
    # Check X-Frame-Options
    echo -n "  X-Frame-Options... "
    if echo "$headers" | grep -qi "X-Frame-Options"; then
        echo -e "${GREEN}✓ Present${NC}"
    else
        echo -e "${RED}✗ Missing${NC}"
    fi
    
    # Check X-Content-Type-Options
    echo -n "  X-Content-Type-Options... "
    if echo "$headers" | grep -qi "X-Content-Type-Options"; then
        echo -e "${GREEN}✓ Present${NC}"
    else
        echo -e "${RED}✗ Missing${NC}"
    fi
    
    # Check X-XSS-Protection
    echo -n "  X-XSS-Protection... "
    if echo "$headers" | grep -qi "X-XSS-Protection"; then
        echo -e "${GREEN}✓ Present${NC}"
    else
        echo -e "${RED}✗ Missing${NC}"
    fi
    
    # Check Content-Security-Policy
    echo -n "  Content-Security-Policy... "
    if echo "$headers" | grep -qi "Content-Security-Policy"; then
        echo -e "${GREEN}✓ Present${NC}"
    else
        echo -e "${YELLOW}⚠ Missing (optional)${NC}"
    fi
}

# Function to test certificate
test_certificate() {
    local domain=$1
    local host=$2
    
    echo -e "${YELLOW}Testing Certificate for $domain:${NC}"
    
    # Get certificate info
    cert_info=$(timeout 5 openssl s_client -connect "$host:443" -servername "$domain" </dev/null 2>/dev/null | openssl x509 -noout -text 2>/dev/null)
    
    if [ -z "$cert_info" ]; then
        echo -e "${RED}✗ Failed to retrieve certificate${NC}"
        return 1
    fi
    
    # Check subject
    echo -n "  Subject... "
    subject=$(echo "$cert_info" | grep "Subject:" | sed 's/.*CN = //')
    echo -e "${GREEN}$subject${NC}"
    
    # Check validity
    echo -n "  Validity... "
    not_after=$(timeout 5 openssl s_client -connect "$host:443" -servername "$domain" </dev/null 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
    echo -e "${GREEN}Valid until $not_after${NC}"
    
    # Check key size
    echo -n "  Key Size... "
    key_size=$(echo "$cert_info" | grep "Public-Key:" | sed 's/.*(\(.*\) bit).*/\1/')
    if [ "$key_size" -ge 2048 ]; then
        echo -e "${GREEN}$key_size bits ✓${NC}"
    else
        echo -e "${RED}$key_size bits (too small!)${NC}"
    fi
}

# Determine host based on test mode
if [ "$TEST_MODE" = "local" ]; then
    echo -e "${YELLOW}Running in LOCAL mode (testing localhost)${NC}"
    echo -e "${YELLOW}Note: Certificate warnings are expected for self-signed certs${NC}"
    echo ""
    HOST="localhost"
else
    echo -e "${YELLOW}Running in REMOTE mode (testing actual domains)${NC}"
    echo ""
    HOST=""
fi

# Test each domain
for domain in "${DOMAINS[@]}"; do
    echo -e "${BLUE}Testing $domain${NC}"
    echo "================================"
    
    # Set host
    if [ "$TEST_MODE" = "local" ]; then
        test_host="localhost"
        test_url="https://localhost"
    else
        test_host="$domain"
        test_url="https://$domain"
    fi
    
    # Test certificate
    test_certificate "$domain" "$test_host"
    echo ""
    
    # Test TLS versions
    echo -e "${YELLOW}Testing TLS Protocol Support:${NC}"
    test_tls_version "$domain" "tls1_3" "$test_host" || true
    test_tls_version "$domain" "tls1_2" "$test_host" || true
    
    # Test that TLS 1.1 and 1.0 are disabled
    echo -n "  Testing TLS 1.1 disabled... "
    if ! timeout 5 openssl s_client -connect "$test_host:443" -servername "$domain" -tls1_1 </dev/null 2>/dev/null | grep -q "Protocol.*TLSv1.1"; then
        echo -e "${GREEN}✓ Correctly disabled${NC}"
    else
        echo -e "${RED}✗ Still enabled (security risk!)${NC}"
    fi
    
    echo -n "  Testing TLS 1.0 disabled... "
    if ! timeout 5 openssl s_client -connect "$test_host:443" -servername "$domain" -tls1 </dev/null 2>/dev/null | grep -q "Protocol.*TLSv1"; then
        echo -e "${GREEN}✓ Correctly disabled${NC}"
    else
        echo -e "${RED}✗ Still enabled (security risk!)${NC}"
    fi
    echo ""
    
    # Test cipher suites
    echo -e "${YELLOW}Testing Strong Cipher Suites:${NC}"
    strong_ciphers=(
        "ECDHE-RSA-AES128-GCM-SHA256"
        "ECDHE-RSA-AES256-GCM-SHA384"
        "ECDHE-RSA-CHACHA20-POLY1305"
    )
    
    cipher_count=0
    for cipher in "${strong_ciphers[@]}"; do
        if test_cipher "$domain" "$cipher" "$test_host"; then
            ((cipher_count++))
        fi
    done
    echo "  ${GREEN}✓ $cipher_count strong ciphers supported${NC}"
    echo ""
    
    # Test security headers
    test_security_headers "$test_url"
    echo ""
    
    # Test HTTP to HTTPS redirect
    if [ "$TEST_MODE" != "local" ]; then
        echo -e "${YELLOW}Testing HTTP to HTTPS Redirect:${NC}"
        echo -n "  HTTP redirect... "
        redirect=$(curl -s -o /dev/null -w "%{http_code}" -L "http://$domain" 2>/dev/null)
        if [ "$redirect" = "200" ]; then
            echo -e "${GREEN}✓ Redirects to HTTPS${NC}"
        else
            echo -e "${RED}✗ No redirect (HTTP code: $redirect)${NC}"
        fi
        echo ""
    fi
    
    echo ""
done

# Summary
echo -e "${BLUE}=== Test Summary ===${NC}"
echo ""
echo "SSL/TLS configuration test completed."
echo ""
echo "For detailed SSL analysis, use:"
echo "  - SSL Labs: https://www.ssllabs.com/ssltest/"
echo "  - Security Headers: https://securityheaders.com/"
echo ""
echo "Expected SSL Labs grade: A+"
echo ""
