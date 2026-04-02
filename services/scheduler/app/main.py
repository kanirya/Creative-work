from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
import uuid

from app.config import get_settings
from app.routers import jobs
from app.models import HealthResponse
from app.services.scheduler import get_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    logger.info("Starting scheduler service")
    scheduler = get_scheduler()
    scheduler.start()
    logger.info("Scheduler started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down scheduler service")
    scheduler.shutdown()
    logger.info("Scheduler stopped")


app = FastAPI(
    title="EduPilot Scheduler Service",
    description="Job scheduling with APScheduler",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
app.include_router(jobs.router, prefix="/api/jobs", tags=["Job Management"])


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    scheduler = get_scheduler()
    active_jobs = len(scheduler.get_jobs())
    
    return HealthResponse(
        status="healthy",
        active_jobs=active_jobs
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "EduPilot Scheduler",
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
