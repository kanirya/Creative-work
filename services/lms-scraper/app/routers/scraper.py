from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from app.models import ScrapeRequest, ScrapingResult, ScrapingStatusResponse, ScrapingStatus
from uuid import UUID
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for scraping status (will be replaced with database)
scraping_status_store = {}


@router.post("/", response_model=ScrapingResult)
async def trigger_scraping(
    request: Request,
    scrape_request: ScrapeRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger LMS scraping for a student
    """
    logger_adapter = request.state.logger
    logger_adapter.info(f"Triggering scraping for student {scrape_request.student_id}")
    
    try:
        # TODO: Implement actual scraping logic
        # This will be implemented in tasks 9.2, 9.3, 9.4
        
        # Store initial status
        scraping_status_store[str(scrape_request.student_id)] = {
            "status": ScrapingStatus.PENDING,
            "last_scraped_at": None,
            "error_message": None
        }
        
        return ScrapingResult(
            student_id=scrape_request.student_id,
            status=ScrapingStatus.PENDING,
            courses_count=0,
            assignments_count=0,
            announcements_count=0
        )
    
    except Exception as e:
        logger_adapter.error(f"Error triggering scraping: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to trigger scraping")


@router.get("/status/{student_id}", response_model=ScrapingStatusResponse)
async def get_scraping_status(request: Request, student_id: UUID):
    """
    Get scraping status for a student
    """
    logger_adapter = request.state.logger
    logger_adapter.info(f"Getting scraping status for student {student_id}")
    
    status_data = scraping_status_store.get(str(student_id))
    
    if not status_data:
        return ScrapingStatusResponse(
            status=ScrapingStatus.PENDING,
            last_scraped_at=None,
            error_message=None
        )
    
    return ScrapingStatusResponse(**status_data)
