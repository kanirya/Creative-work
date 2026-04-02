"""
Prometheus metrics middleware for FastAPI services.
Tracks HTTP request metrics including response times, error rates, and request counts.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from fastapi.responses import Response as FastAPIResponse
import time
from typing import Callable

# Define Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

REQUEST_IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)

ERROR_COUNT = Counter(
    'http_errors_total',
    'Total HTTP errors',
    ['method', 'endpoint', 'status']
)


async def prometheus_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to collect Prometheus metrics for each HTTP request.
    
    Tracks:
    - Request count by method, endpoint, and status
    - Request duration by method and endpoint
    - Requests in progress
    - Error count by method, endpoint, and status
    """
    # Skip metrics endpoint itself
    if request.url.path == "/metrics":
        return await call_next(request)
    
    method = request.method
    endpoint = request.url.path
    
    # Track requests in progress
    REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        status = response.status_code
        
        # Record metrics
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        
        duration = time.time() - start_time
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        
        # Track errors (4xx and 5xx)
        if status >= 400:
            ERROR_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        
        return response
    
    except Exception as e:
        # Track unhandled exceptions
        ERROR_COUNT.labels(method=method, endpoint=endpoint, status=500).inc()
        raise
    
    finally:
        # Decrement in-progress counter
        REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()


def metrics_endpoint() -> FastAPIResponse:
    """
    Endpoint to expose Prometheus metrics.
    Returns metrics in Prometheus text format.
    """
    return FastAPIResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
