from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import uuid

from app.config import get_settings
from app.routers import scraper
from app.routers import lms as lms_router
from app.models import HealthResponse
from app.middleware.metrics import prometheus_middleware, metrics_endpoint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="EduPilot LMS Scraper Service",
    description="Automated LMS data scraping with Playwright",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics middleware
app.middleware("http")(prometheus_middleware)


# Correlation ID middleware
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    
    # Add to logging context
    logger_adapter = logging.LoggerAdapter(logger, {"correlation_id": correlation_id})
    request.state.logger = logger_adapter
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Process-Time"] = str(process_time)
    
    logger_adapter.info(f"Request completed in {process_time:.3f}s")
    
    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.error(f"Unhandled exception: {str(exc)}", extra={"correlation_id": correlation_id}, exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An internal error occurred",
            "correlation_id": correlation_id
        }
    )


# Include routers
app.include_router(scraper.router, prefix="/api/scrape", tags=["LMS Scraping"])
app.include_router(lms_router.router, prefix="/api/lms", tags=["LMS Operations"])


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy")


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return metrics_endpoint()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "EduPilot LMS Scraper",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=True
    )
