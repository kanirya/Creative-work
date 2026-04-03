#!/bin/bash

# EduPilot SSL Certificate Setup Script
# This script generates self-signed certificates for development
# For production, use Let's Encrypt with certbot

set -e

echo "=== EduPilot SSL Certificate Setup ==="
echo ""

# Configuration
SSL_DIR="./ssl"
DOMAINS=("api.edupilot.com" "app.edupilot.com" "edupilot.com")
DAYS_VALID=365
COUNTRY="PK"
STATE="Sindh"
CITY="Karachi"
ORG="Agentix"
OU="EduPilot"

# Create SSL directory structure
echo "Creating SSL directory structure..."
mkdir -p "$SSL_DIR"

for domain in "${DOMAINS[@]}"; do
    echo ""
    echo "Generating certificate for $domain..."
    
    DOMAIN_DIR="$SSL_DIR/$domain"
    mkdir -p "$DOMAIN_DIR"
    
    # Generate private key
    openssl genrsa -out "$DOMAIN_DIR/privkey.pem" 4096
    
    # Generate certificate signing request
    openssl req -new -key "$DOMAIN_DIR/privkey.pem" \
        -out "$DOMAIN_DIR/csr.pem" \
        -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU/CN=$domain"
    
    # Generate self-signed certificate
    openssl x509 -req -days $DAYS_VALID \
        -in "$DOMAIN_DIR/csr.pem" \
        -signkey "$DOMAIN_DIR/privkey.pem" \
        -out "$DOMAIN_DIR/fullchain.pem"
    
    # Create chain file (for self-signed, same as cert)
    cp "$DOMAIN_DIR/fullchain.pem" "$DOMAIN_DIR/chain.pem"
    
    # Set proper permissions
    chmod 600 "$DOMAIN_DIR/privkey.pem"
    chmod 644 "$DOMAIN_DIR/fullchain.pem"
    chmod 644 "$DOMAIN_DIR/chain.pem"
    
    echo "✓ Certificate generated for $domain"
done

echo ""
echo "=== SSL Certificate Setup Complete ==="
echo ""
echo "Certificates generated in: $SSL_DIR"
echo ""
echo "⚠️  IMPORTANT: These are self-signed certificates for development only!"
echo "For production, use Let's Encrypt with certbot:"
echo "  ./nginx/setup-letsencrypt.sh"
echo ""
