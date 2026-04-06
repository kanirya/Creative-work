FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Playwright dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    wget \
    gnupg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright system dependencies and Chromium browser
RUN playwright install-deps chromium && playwright install chromium

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copy application code
COPY app/ ./app/

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8002/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
