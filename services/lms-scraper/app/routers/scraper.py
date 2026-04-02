from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from app.models import ScrapeRequest, ScrapingResult, ScrapingStatusResponse, ScrapingStatus
from app.services.lms_auth import get_lms_auth_service, LMSAuthenticationError
from app.services.scrapers import LMSScrapers
from app.services.data_storage import get_data_storage_service
from uuid import UUID
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for scraping status
scraping_status_store = {}


async def perform_scraping(student_id: UUID, username: str, password: str):
    """Background task to perform scraping"""
    logger.info(f"Starting background scraping for student {student_id}")
    
    # Update status to in_progress
    scraping_status_store[str(student_id)] = {
        "status": ScrapingStatus.IN_PROGRESS,
        "last_scraped_at": None,
        "error_message": None
    }
    
    auth_service = get_lms_auth_service()
    storage_service = get_data_storage_service()
    
    try:
        # Authenticate
        context = await auth_service.authenticate(username, password)
        
        # Create scrapers
        scrapers = LMSScrapers(context)
        
        # Scrape data
        courses = await scrapers.scrape_courses()
        assignments = await scrapers.scrape_assignments()
        announcements = await scrapers.scrape_announcements()
        
        # Store data and generate embeddings
        courses_count = await storage_service.store_courses(student_id, courses)
        assignments_count = await storage_service.store_assignments(student_id, assignments)
        announcements_count = await storage_service.store_announcements(student_id, announcements)
        
        # Update status to completed
        scraping_status_store[str(student_id)] = {
            "status": ScrapingStatus.COMPLETED,
            "last_scraped_at": datetime.utcnow(),
            "error_message": None,
            "courses_count": courses_count,
            "assignments_count": assignments_count,
            "announcements_count": announcements_count
        }
        
        logger.info(f"Scraping completed for student {student_id}")
        
    except LMSAuthenticationError as e:
        logger.error(f"Authentication failed for student {student_id}: {str(e)}")
        scraping_status_store[str(student_id)] = {
            "status": ScrapingStatus.FAILED,
            "last_scraped_at": None,
            "error_message": f"Authentication failed: {str(e)}"
        }
    
    except Exception as e:
        logger.error(f"Scraping failed for student {student_id}: {str(e)}", exc_info=True)
        scraping_status_store[str(student_id)] = {
            "status": ScrapingStatus.FAILED,
            "last_scraped_at": None,
            "error_message": str(e)
        }
    
    finally:
        await auth_service.close_browser()


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
        # Store initial status
        scraping_status_store[str(scrape_request.student_id)] = {
            "status": ScrapingStatus.PENDING,
            "last_scraped_at": None,
            "error_message": None
        }
        
        # Add scraping task to background
        background_tasks.add_task(
            perform_scraping,
            scrape_request.student_id,
            scrape_request.lms_username,
            scrape_request.lms_password
        )
        
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
