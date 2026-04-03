# Multi-stage Dockerfile for Marketing Site
# Stage 1: Dependencies and Builder
FROM node:20-alpine AS builder
WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy all package files
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml* ./
COPY turbo.json ./
COPY tsconfig.json .eslintrc.json .prettierrc* ./
COPY apps/marketing ./apps/marketing

# Install all dependencies
RUN pnpm install --frozen-lockfile

# Build the application (static export) using turbo
ENV NEXT_TELEMETRY_DISABLED 1
RUN pnpm turbo build --filter=@edupilot/marketing

# Stage 2: Production with nginx
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
