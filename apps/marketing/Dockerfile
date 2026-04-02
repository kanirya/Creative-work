# Multi-stage Dockerfile for Marketing Site
# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./
COPY apps/marketing/package.json ./apps/marketing/

# Install dependencies
RUN npm install --workspace=@edupilot/marketing --include-workspace-root

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/apps/marketing/node_modules ./apps/marketing/node_modules

# Copy source code
COPY turbo.json ./
COPY apps/marketing ./apps/marketing

# Build the application (static export)
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build --workspace=@edupilot/marketing

# Stage 3: Production with nginx
FROM nginx:alpine AS runner

WORKDIR /usr/share/nginx/html

# Copy static files from builder
COPY --from=builder /app/apps/marketing/out ./

# Copy nginx configuration
COPY apps/marketing/nginx.conf /etc/nginx/nginx.conf

# Create non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser && \
    chown -R appuser:appuser /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx/conf.d

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

# Switch to non-root user
USER appuser

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
