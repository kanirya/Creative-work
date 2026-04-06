"""
Scraper API router.
Triggers Moodle scraping jobs and returns status/results.
"""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app.models import (
    ScrapingResult,
    ScrapingStatus,
    ScrapingStatusResponse,
    ScrapeRequest,
)
from app.services.data_storage import get_data_storage_service
from app.services.lms_auth import (
    LMSAuthenticationError,
    MFARequiredError,
    PasswordChangeRequiredError,
    get_lms_auth_service,
)
from app.services.scrapers import MoodleScrapers

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory scraping status store (replace with Redis in production)
_status_store: dict = {}


# ── Background scraping task ──────────────────────────────────────────────────


async def _perform_scraping(student_id: UUID, scrape_types: list):
    """Full scraping pipeline: auth → scrape all data types → store."""
    logger.info(f"Starting scraping pipeline for student {student_id}")

    _status_store[str(student_id)] = {
        "status": ScrapingStatus.IN_PROGRESS,
        "last_scraped_at": None,
        "error_message": None,
        "courses_count": 0,
        "assignments_count": 0,
        "grades_count": 0,
    }

    auth_service = get_lms_auth_service()
    storage = get_data_storage_service()

    try:
        # ── Authenticate ──────────────────────────────────────────────────────
        context = await auth_service.get_authenticated_context()
        scrapers = MoodleScrapers(context)

        courses = []
        assignments_count = grades_count = announcements_count = events_count = quizzes_count = 0

        # ── Scrape courses (always first — other scrapers depend on it) ───────
        if "courses" in scrape_types:
            courses = await scrapers.scrape_courses()
            courses_count = await storage.store_courses(student_id, courses)
        else:
            courses_count = 0

        # ── Scrape assignments ────────────────────────────────────────────────
        if "assignments" in scrape_types and courses:
            assignments = await scrapers.scrape_assignments(courses)
            assignments_count = await storage.store_assignments(student_id, assignments)

        # ── Scrape grades ─────────────────────────────────────────────────────
        if "grades" in scrape_types and courses:
            grades = await scrapers.scrape_grades(courses)
            grades_count = await storage.store_grades(student_id, grades)

        # ── Scrape announcements ──────────────────────────────────────────────
        if "announcements" in scrape_types and courses:
            announcements = await scrapers.scrape_announcements(courses)
            announcements_count = await storage.store_announcements(student_id, announcements)

        # ── Scrape schedule ───────────────────────────────────────────────────
        if "schedule" in scrape_types:
            events = await scrapers.scrape_schedule()
            events_count = await storage.store_schedule_events(student_id, events)

        # ── Scrape quizzes ────────────────────────────────────────────────────
        if "quizzes" in scrape_types and courses:
            quizzes = await scrapers.scrape_quizzes(courses)
            quizzes_count = await storage.store_quizzes(student_id, quizzes)

        _status_store[str(student_id)] = {
            "status": ScrapingStatus.COMPLETED,
            "last_scraped_at": datetime.utcnow(),
            "error_message": None,
            "courses_count": courses_count,
            "assignments_count": assignments_count,
            "grades_count": grades_count,
        }
        logger.info(
            f"Scraping completed for student {student_id}: "
            f"{courses_count} courses, {assignments_count} assignments, "
            f"{grades_count} grades, {announcements_count} announcements, "
            f"{events_count} events, {quizzes_count} quizzes"
        )

    except MFARequiredError as e:
        logger.error(f"MFA required for student {student_id}: {e}")
        _status_store[str(student_id)].update(
            status=ScrapingStatus.FAILED,
            error_message=f"MFA required: {e}",
        )
    except PasswordChangeRequiredError as e:
        logger.error(f"Password change required for student {student_id}: {e}")
        _status_store[str(student_id)].update(
            status=ScrapingStatus.FAILED,
            error_message=f"Password change required: {e}",
        )
    except LMSAuthenticationError as e:
        logger.error(f"Authentication failed for student {student_id}: {e}")
        _status_store[str(student_id)].update(
            status=ScrapingStatus.FAILED,
            error_message=f"Authentication failed: {e}",
        )
    except Exception as e:
        logger.error(f"Scraping failed for student {student_id}: {e}", exc_info=True)
        _status_store[str(student_id)].update(
            status=ScrapingStatus.FAILED,
            error_message=str(e),
        )
    finally:
        await auth_service.close()


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/", response_model=ScrapingResult)
async def trigger_scraping(
    request: Request,
    scrape_request: ScrapeRequest,
    background_tasks: BackgroundTasks,
):
    """Trigger LMS scraping for a student (runs in background)."""
    logger.info(f"Triggering scraping for student {scrape_request.student_id}")

    _status_store[str(scrape_request.student_id)] = {
        "status": ScrapingStatus.PENDING,
        "last_scraped_at": None,
        "error_message": None,
        "courses_count": 0,
        "assignments_count": 0,
        "grades_count": 0,
    }

    background_tasks.add_task(
        _perform_scraping,
        scrape_request.student_id,
        scrape_request.scrape_types,
    )

    return ScrapingResult(
        student_id=scrape_request.student_id,
        status=ScrapingStatus.PENDING,
    )


@router.get("/status/{student_id}", response_model=ScrapingStatusResponse)
async def get_scraping_status(request: Request, student_id: UUID):
    """Get current scraping status for a student."""
    data = _status_store.get(str(student_id), {})
    return ScrapingStatusResponse(
        status=data.get("status", ScrapingStatus.PENDING),
        last_scraped_at=data.get("last_scraped_at"),
        error_message=data.get("error_message"),
        courses_count=data.get("courses_count", 0),
        assignments_count=data.get("assignments_count", 0),
        grades_count=data.get("grades_count", 0),
    )


@router.get("/results/{student_id}")
async def get_scraping_results(student_id: UUID):
    """Return last scraping summary for a student."""
    data = _status_store.get(str(student_id))
    if not data:
        return {"student_id": str(student_id), "message": "No scraping data found"}
    return {
        "student_id": str(student_id),
        "status": data.get("status"),
        "last_scraped_at": data.get("last_scraped_at"),
        "courses_count": data.get("courses_count", 0),
        "assignments_count": data.get("assignments_count", 0),
        "grades_count": data.get("grades_count", 0),
        "error_message": data.get("error_message"),
    }
