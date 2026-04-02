# Multi-stage Dockerfile for Student Web App
# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./
COPY apps/web/package.json ./apps/web/
COPY packages/api-client/package.json ./packages/api-client/
COPY packages/types/package.json ./packages/types/
COPY packages/ui/package.json ./packages/ui/
COPY packages/utils/package.json ./packages/utils/

# Install dependencies
RUN npm install --workspace=@edupilot/web --include-workspace-root

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/apps/web/node_modules ./apps/web/node_modules
COPY --from=deps /app/packages ./packages

# Copy source code
COPY turbo.json ./
COPY apps/web ./apps/web
COPY packages ./packages

# Build the application
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build --workspace=@edupilot/web

# Stage 3: Production with nginx
FROM nginx:alpine AS runner

# Install Node.js for Next.js standalone server
RUN apk add --no-cache nodejs

WORKDIR /app

# Copy built application
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder /app/apps/web/public ./apps/web/public

# Copy nginx configuration
COPY apps/web/nginx.conf /etc/nginx/nginx.conf

# Create non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser && \
    chown -R appuser:appuser /app /var/cache/nginx /var/log/nginx /etc/nginx/conf.d

# Expose ports
EXPOSE 3000 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/api/health || exit 1

# Switch to non-root user
USER appuser

# Start both Next.js server and nginx
CMD ["sh", "-c", "node apps/web/server.js & nginx -g 'daemon off;'"]
