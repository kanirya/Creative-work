#!/bin/bash

# EduPilot Let's Encrypt SSL Certificate Setup Script
# This script sets up automatic SSL certificate generation and renewal using certbot

set -e

echo "=== EduPilot Let's Encrypt SSL Setup ==="
echo ""

# Configuration
DOMAINS=("api.edupilot.com" "app.edupilot.com" "edupilot.com" "www.edupilot.com")
EMAIL="admin@edupilot.com"
SSL_DIR="./ssl"
WEBROOT="/var/www/certbot"

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo "Error: certbot is not installed"
    echo "Install certbot:"
    echo "  Ubuntu/Debian: sudo apt-get install certbot"
    echo "  CentOS/RHEL: sudo yum install certbot"
    echo "  macOS: brew install certbot"
    exit 1
fi

# Create webroot directory for ACME challenge
echo "Creating webroot directory for ACME challenge..."
mkdir -p "$WEBROOT"

# Create SSL directory
mkdir -p "$SSL_DIR"

echo ""
echo "⚠️  IMPORTANT: Before running this script, ensure:"
echo "  1. DNS records for all domains point to this server"
echo "  2. Ports 80 and 443 are open in firewall"
echo "  3. nginx is running with HTTP server for ACME challenge"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Generate certificates for each domain
for domain in "${DOMAINS[@]}"; do
    echo ""
    echo "Generating Let's Encrypt certificate for $domain..."
    
    # Request certificate
    sudo certbot certonly \
        --webroot \
        --webroot-path="$WEBROOT" \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --force-renewal \
        -d "$domain"
    
    # Copy certificates to nginx SSL directory
    DOMAIN_DIR="$SSL_DIR/$domain"
    mkdir -p "$DOMAIN_DIR"
    
    sudo cp "/etc/letsencrypt/live/$domain/fullchain.pem" "$DOMAIN_DIR/fullchain.pem"
    sudo cp "/etc/letsencrypt/live/$domain/privkey.pem" "$DOMAIN_DIR/privkey.pem"
    sudo cp "/etc/letsencrypt/live/$domain/chain.pem" "$DOMAIN_DIR/chain.pem"
    
    # Set proper permissions
    sudo chmod 644 "$DOMAIN_DIR/fullchain.pem"
    sudo chmod 600 "$DOMAIN_DIR/privkey.pem"
    sudo chmod 644 "$DOMAIN_DIR/chain.pem"
    
    echo "✓ Certificate generated for $domain"
done

# Set up automatic renewal
echo ""
echo "Setting up automatic certificate renewal..."

# Create renewal script
cat > ./nginx/renew-certificates.sh << 'EOF'
#!/bin/bash
# Auto-renewal script for Let's Encrypt certificates

set -e

echo "Renewing Let's Encrypt certificates..."
sudo certbot renew --quiet

# Copy renewed certificates to nginx SSL directory
SSL_DIR="./ssl"
DOMAINS=("api.edupilot.com" "app.edupilot.com" "edupilot.com" "www.edupilot.com")

for domain in "${DOMAINS[@]}"; do
    if [ -d "/etc/letsencrypt/live/$domain" ]; then
        DOMAIN_DIR="$SSL_DIR/$domain"
        sudo cp "/etc/letsencrypt/live/$domain/fullchain.pem" "$DOMAIN_DIR/fullchain.pem"
        sudo cp "/etc/letsencrypt/live/$domain/privkey.pem" "$DOMAIN_DIR/privkey.pem"
        sudo cp "/etc/letsencrypt/live/$domain/chain.pem" "$DOMAIN_DIR/chain.pem"
        echo "✓ Renewed certificate for $domain"
    fi
done

# Reload nginx to use new certificates
docker-compose exec nginx nginx -s reload
echo "✓ nginx reloaded"
EOF

chmod +x ./nginx/renew-certificates.sh

# Add cron job for automatic renewal (runs daily at 2 AM)
echo ""
echo "Adding cron job for automatic renewal..."
CRON_JOB="0 2 * * * cd $(pwd) && ./nginx/renew-certificates.sh >> ./nginx/renewal.log 2>&1"

# Check if cron job already exists
if ! crontab -l 2>/dev/null | grep -q "renew-certificates.sh"; then
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✓ Cron job added"
else
    echo "✓ Cron job already exists"
fi

echo ""
echo "=== Let's Encrypt SSL Setup Complete ==="
echo ""
echo "Certificates generated in: $SSL_DIR"
echo "Automatic renewal configured to run daily at 2 AM"
echo ""
echo "To manually renew certificates, run:"
echo "  ./nginx/renew-certificates.sh"
echo ""
echo "To test renewal (dry run):"
echo "  sudo certbot renew --dry-run"
echo ""
