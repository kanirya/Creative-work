# Nginx Reverse Proxy Dockerfile
FROM nginx:1.25-alpine

# Install required packages
RUN apk add --no-cache \
    openssl \
    ca-certificates \
    curl

# Remove default nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create directories for SSL certificates
RUN mkdir -p /etc/nginx/ssl/api.edupilot.com \
    /etc/nginx/ssl/app.edupilot.com \
    /etc/nginx/ssl/edupilot.com \
    /var/www/certbot

# Create self-signed certificates for development
# In production, these should be replaced with real certificates from Let's Encrypt
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/api.edupilot.com/privkey.pem \
    -out /etc/nginx/ssl/api.edupilot.com/fullchain.pem \
    -subj "/C=PK/ST=Sindh/L=Karachi/O=EduPilot/CN=api.edupilot.com" && \
    cp /etc/nginx/ssl/api.edupilot.com/fullchain.pem /etc/nginx/ssl/api.edupilot.com/chain.pem

RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/app.edupilot.com/privkey.pem \
    -out /etc/nginx/ssl/app.edupilot.com/fullchain.pem \
    -subj "/C=PK/ST=Sindh/L=Karachi/O=EduPilot/CN=app.edupilot.com" && \
    cp /etc/nginx/ssl/app.edupilot.com/fullchain.pem /etc/nginx/ssl/app.edupilot.com/chain.pem

RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/edupilot.com/privkey.pem \
    -out /etc/nginx/ssl/edupilot.com/fullchain.pem \
    -subj "/C=PK/ST=Sindh/L=Karachi/O=EduPilot/CN=edupilot.com" && \
    cp /etc/nginx/ssl/edupilot.com/fullchain.pem /etc/nginx/ssl/edupilot.com/chain.pem

# Create nginx user and set permissions
RUN chown -R nginx:nginx /var/cache/nginx /var/log/nginx /etc/nginx/ssl

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Expose ports
EXPOSE 80 443

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
