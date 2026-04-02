#!/bin/bash
# SSL Certificate Setup Script for EduPilot
# This script helps set up Let's Encrypt SSL certificates for production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOMAINS=("api.edupilot.com" "app.edupilot.com" "edupilot.com" "www.edupilot.com")
EMAIL="${SSL_EMAIL:-admin@edupilot.com}"
STAGING="${STAGING:-0}"

echo -e "${GREEN}EduPilot SSL Certificate Setup${NC}"
echo "================================"
echo ""

# Check if running in production mode
if [ "$STAGING" = "1" ]; then
    echo -e "${YELLOW}Running in STAGING mode (test certificates)${NC}"
    STAGING_FLAG="--staging"
else
    echo -e "${GREEN}Running in PRODUCTION mode (real certificates)${NC}"
    STAGING_FLAG=""
fi

echo "Email: $EMAIL"
echo "Domains: ${DOMAINS[*]}"
echo ""

# Confirm before proceeding
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Function to obtain certificate for a domain
obtain_certificate() {
    local domain=$1
    echo -e "${GREEN}Obtaining certificate for $domain...${NC}"
    
    docker run -it --rm \
        --name certbot \
        -v nginx-ssl:/etc/letsencrypt \
        -v certbot-webroot:/var/www/certbot \
        certbot/certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        $STAGING_FLAG \
        -d "$domain"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Certificate obtained for $domain${NC}"
        
        # Copy certificates to nginx ssl directory
        docker run --rm \
            -v nginx-ssl:/etc/letsencrypt \
            alpine sh -c "
                mkdir -p /etc/letsencrypt/live/$domain
                cp /etc/letsencrypt/live/$domain/fullchain.pem /etc/letsencrypt/live/$domain/fullchain.pem
                cp /etc/letsencrypt/live/$domain/privkey.pem /etc/letsencrypt/live/$domain/privkey.pem
                cp /etc/letsencrypt/live/$domain/chain.pem /etc/letsencrypt/live/$domain/chain.pem
            "
    else
        echo -e "${RED}✗ Failed to obtain certificate for $domain${NC}"
        return 1
    fi
}

# Obtain certificates for all domains
for domain in "${DOMAINS[@]}"; do
    obtain_certificate "$domain"
    echo ""
done

echo -e "${GREEN}Certificate setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Update nginx configuration to use the new certificates"
echo "2. Reload nginx: docker exec edupilot-nginx nginx -s reload"
echo "3. Set up automatic renewal (see README.md)"
echo ""
echo "To set up automatic renewal, add this to your crontab:"
echo "0 0 * * * docker run --rm -v nginx-ssl:/etc/letsencrypt -v certbot-webroot:/var/www/certbot certbot/certbot renew --quiet && docker exec edupilot-nginx nginx -s reload"
