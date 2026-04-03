#!/bin/bash
# Auto-renewal script for Let's Encrypt certificates
# This script is designed to run via cron job daily

set -e

# Configuration
SSL_DIR="./ssl"
DOMAINS=("api.edupilot.com" "app.edupilot.com" "edupilot.com" "www.edupilot.com")
LOG_FILE="./nginx/renewal.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting certificate renewal process..."

# Renew certificates using certbot
log "Running certbot renew..."
if sudo certbot renew --quiet; then
    log "✓ Certbot renewal completed successfully"
else
    log "✗ Certbot renewal failed"
    exit 1
fi

# Copy renewed certificates to nginx SSL directory
log "Copying renewed certificates to nginx SSL directory..."
for domain in "${DOMAINS[@]}"; do
    if [ -d "/etc/letsencrypt/live/$domain" ]; then
        DOMAIN_DIR="$SSL_DIR/$domain"
        mkdir -p "$DOMAIN_DIR"
        
        sudo cp "/etc/letsencrypt/live/$domain/fullchain.pem" "$DOMAIN_DIR/fullchain.pem"
        sudo cp "/etc/letsencrypt/live/$domain/privkey.pem" "$DOMAIN_DIR/privkey.pem"
        sudo cp "/etc/letsencrypt/live/$domain/chain.pem" "$DOMAIN_DIR/chain.pem"
        
        # Set proper permissions
        sudo chmod 644 "$DOMAIN_DIR/fullchain.pem"
        sudo chmod 600 "$DOMAIN_DIR/privkey.pem"
        sudo chmod 644 "$DOMAIN_DIR/chain.pem"
        
        log "✓ Renewed certificate for $domain"
    else
        log "⚠ Certificate directory not found for $domain"
    fi
done

# Reload nginx to use new certificates
log "Reloading nginx..."
if docker-compose exec -T nginx nginx -s reload 2>/dev/null; then
    log "✓ nginx reloaded successfully"
elif docker exec edupilot-nginx nginx -s reload 2>/dev/null; then
    log "✓ nginx reloaded successfully"
else
    log "✗ Failed to reload nginx"
    exit 1
fi

log "Certificate renewal process completed successfully"
