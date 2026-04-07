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
from app.middleware.metrics import prometheus_middleware, metrics_endpoint

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

    # Schedule scraping jobs for all active students on startup
    await _schedule_all_student_scraping_jobs(scheduler)

    yield

    # Shutdown
    logger.info("Shutting down scheduler service")
    scheduler.shutdown()
    logger.info("Scheduler stopped")


async def _schedule_all_student_scraping_jobs(scheduler):
    """
    On startup, schedule a scraping job every 6 hours for all active students.
    Reads student list from the database via the API Gateway.
    """
    import httpx
    from apscheduler.triggers.interval import IntervalTrigger
    from app.services.job_executor import get_job_executor

    api_gateway_url = settings.lms_scraper_url.replace(":8002", ":8080").replace("lms-scraper", "api-gateway")
    # Fallback: use env var if available
    import os
    api_gateway_url = os.getenv("API_GATEWAY_URL", "http://api-gateway:8080")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{api_gateway_url}/api/v1/admin/students/active")
            if resp.status_code == 200:
                students = resp.json().get("data", [])
                executor = get_job_executor()
                for student in students:
                    student_id = student.get("id")
                    if not student_id:
                        continue
                    from uuid import UUID
                    import random
                    # Add jitter: ±30 minutes to avoid thundering herd
                    jitter_minutes = random.randint(-30, 30)
                    interval_seconds = settings.scraping_interval_hours * 3600 + jitter_minutes * 60

                    scheduler.add_job(
                        func=executor.execute_scraping_job_with_retry,
                        trigger=IntervalTrigger(seconds=interval_seconds),
                        job_id=f"scraping_{student_id}",
                        job_type="scraping",
                        student_id=UUID(student_id),
                        kwargs={"job_id": UUID(student_id), "student_id": UUID(student_id)},
                    )
                    logger.info(f"Scheduled scraping job for student {student_id} every {interval_seconds}s")
                logger.info(f"Scheduled scraping jobs for {len(students)} active students")
            else:
                logger.warning(f"Could not fetch active students (status {resp.status_code}). Scraping jobs not scheduled.")
    except Exception as e:
        logger.warning(f"Could not schedule student scraping jobs on startup: {e}")


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


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return metrics_endpoint()


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
