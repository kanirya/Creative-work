# Multi-stage Dockerfile for Student Web App
# Stage 1: Dependencies and Builder
FROM node:20-alpine AS builder
WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy all package files
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml* ./
COPY turbo.json ./
COPY tsconfig.json .eslintrc.json .prettierrc* ./
COPY apps/web ./apps/web
COPY packages ./packages

# Create public directory if it doesn't exist
RUN mkdir -p apps/web/public

# Install all dependencies
RUN pnpm install --frozen-lockfile

# Build using turbo (will build dependencies first)
ENV NEXT_TELEMETRY_DISABLED 1
RUN pnpm turbo build --filter=@edupilot/web

# Stage 2: Production with nginx
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
