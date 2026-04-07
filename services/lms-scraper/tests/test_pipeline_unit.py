"""
Mock-based unit tests for the full scraping pipeline (_perform_scraping).
These tests do NOT require real LMS credentials or a browser.
"""

import sys
from unittest.mock import MagicMock

# Stub out heavy dependencies before any app imports
for mod in ["psycopg2", "psycopg2.extras", "langchain_openai", "prometheus_client"]:
    sys.modules.setdefault(mod, MagicMock())

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import UUID

from app.models import ScrapingStatus
from app.services.lms_auth import LMSAuthenticationError


STUDENT_ID = UUID("12345678-1234-5678-1234-567812345678")


def make_mock_storage():
    storage = AsyncMock()
    storage.store_courses = AsyncMock(return_value=3)
    storage.store_assignments = AsyncMock(return_value=5)
    storage.store_grades = AsyncMock(return_value=10)
    storage.store_announcements = AsyncMock(return_value=2)
    storage.store_schedule_events = AsyncMock(return_value=4)
    storage.store_quizzes = AsyncMock(return_value=1)
    return storage


def make_mock_scrapers(courses=None):
    from app.models import CourseData
    if courses is None:
        courses = [
            CourseData(course_id=101, course_code="CS-301", course_name="Data Structures"),
            CourseData(course_id=102, course_code="MGT-401", course_name="Management"),
        ]
    scrapers = AsyncMock()
    scrapers.scrape_courses = AsyncMock(return_value=courses)
    scrapers.scrape_assignments = AsyncMock(return_value=[])
    scrapers.scrape_grades = AsyncMock(return_value=[])
    scrapers.scrape_announcements = AsyncMock(return_value=[])
    scrapers.scrape_schedule = AsyncMock(return_value=[])
    scrapers.scrape_quizzes = AsyncMock(return_value=[])
    return scrapers


@pytest.mark.asyncio
async def test_successful_scraping_sets_status_completed():
    """Successful scraping pipeline should set status to COMPLETED."""
    from app.routers.scraper import _perform_scraping, _status_store

    mock_context = AsyncMock()
    mock_auth = AsyncMock()
    mock_auth.get_authenticated_context = AsyncMock(return_value=mock_context)
    mock_auth.close = AsyncMock()

    mock_storage = make_mock_storage()
    mock_scrapers = make_mock_scrapers()

    with patch("app.routers.scraper.get_lms_auth_service", return_value=mock_auth), \
         patch("app.routers.scraper.get_data_storage_service", return_value=mock_storage), \
         patch("app.routers.scraper.MoodleScrapers", return_value=mock_scrapers):

        await _perform_scraping(STUDENT_ID, ["courses", "assignments", "grades"])

    status = _status_store.get(str(STUDENT_ID), {})
    assert status["status"] == ScrapingStatus.COMPLETED
    assert status["error_message"] is None
    assert status["courses_count"] == 3
    assert status["assignments_count"] == 5
    assert status["grades_count"] == 10


@pytest.mark.asyncio
async def test_auth_failure_sets_status_failed():
    """Authentication failure should set status to FAILED with correct error message."""
    from app.routers.scraper import _perform_scraping, _status_store

    mock_auth = AsyncMock()
    mock_auth.get_authenticated_context = AsyncMock(
        side_effect=LMSAuthenticationError("Invalid credentials")
    )
    mock_auth.close = AsyncMock()

    mock_storage = make_mock_storage()

    with patch("app.routers.scraper.get_lms_auth_service", return_value=mock_auth), \
         patch("app.routers.scraper.get_data_storage_service", return_value=mock_storage):

        await _perform_scraping(STUDENT_ID, ["courses", "assignments"])

    status = _status_store.get(str(STUDENT_ID), {})
    assert status["status"] == ScrapingStatus.FAILED
    assert "Authentication failed" in status["error_message"]
    assert "Invalid credentials" in status["error_message"]


@pytest.mark.asyncio
async def test_partial_scraper_failure_stores_partial_results():
    """If one scraper fails, the pipeline should still store results from successful scrapers."""
    from app.routers.scraper import _perform_scraping, _status_store

    mock_context = AsyncMock()
    mock_auth = AsyncMock()
    mock_auth.get_authenticated_context = AsyncMock(return_value=mock_context)
    mock_auth.close = AsyncMock()

    mock_storage = make_mock_storage()
    mock_scrapers = make_mock_scrapers()
    # Grades scraper raises an exception
    mock_scrapers.scrape_grades = AsyncMock(side_effect=Exception("Grades page unavailable"))

    with patch("app.routers.scraper.get_lms_auth_service", return_value=mock_auth), \
         patch("app.routers.scraper.get_data_storage_service", return_value=mock_storage), \
         patch("app.routers.scraper.MoodleScrapers", return_value=mock_scrapers):

        await _perform_scraping(STUDENT_ID, ["courses", "assignments", "grades"])

    status = _status_store.get(str(STUDENT_ID), {})
    # Pipeline should still complete (or fail gracefully)
    # courses and assignments were stored
    mock_storage.store_courses.assert_called_once()
    mock_storage.store_assignments.assert_called_once()


@pytest.mark.asyncio
async def test_scraping_calls_auth_close_on_success():
    """Auth service close() should always be called after scraping."""
    from app.routers.scraper import _perform_scraping

    mock_context = AsyncMock()
    mock_auth = AsyncMock()
    mock_auth.get_authenticated_context = AsyncMock(return_value=mock_context)
    mock_auth.close = AsyncMock()

    mock_storage = make_mock_storage()
    mock_scrapers = make_mock_scrapers()

    with patch("app.routers.scraper.get_lms_auth_service", return_value=mock_auth), \
         patch("app.routers.scraper.get_data_storage_service", return_value=mock_storage), \
         patch("app.routers.scraper.MoodleScrapers", return_value=mock_scrapers):

        await _perform_scraping(STUDENT_ID, ["courses"])

    mock_auth.close.assert_called_once()


@pytest.mark.asyncio
async def test_scraping_calls_auth_close_on_auth_failure():
    """Auth service close() should be called even when auth fails."""
    from app.routers.scraper import _perform_scraping

    mock_auth = AsyncMock()
    mock_auth.get_authenticated_context = AsyncMock(
        side_effect=LMSAuthenticationError("Blocked")
    )
    mock_auth.close = AsyncMock()

    mock_storage = make_mock_storage()

    with patch("app.routers.scraper.get_lms_auth_service", return_value=mock_auth), \
         patch("app.routers.scraper.get_data_storage_service", return_value=mock_storage):

        await _perform_scraping(STUDENT_ID, ["courses"])

    mock_auth.close.assert_called_once()


@pytest.mark.asyncio
async def test_scraping_only_requested_types():
    """Only the requested scrape types should be executed."""
    from app.routers.scraper import _perform_scraping

    mock_context = AsyncMock()
    mock_auth = AsyncMock()
    mock_auth.get_authenticated_context = AsyncMock(return_value=mock_context)
    mock_auth.close = AsyncMock()

    mock_storage = make_mock_storage()
    mock_scrapers = make_mock_scrapers()

    with patch("app.routers.scraper.get_lms_auth_service", return_value=mock_auth), \
         patch("app.routers.scraper.get_data_storage_service", return_value=mock_storage), \
         patch("app.routers.scraper.MoodleScrapers", return_value=mock_scrapers):

        await _perform_scraping(STUDENT_ID, ["courses"])

    # Only courses should be scraped
    mock_scrapers.scrape_courses.assert_called_once()
    mock_scrapers.scrape_assignments.assert_not_called()
    mock_scrapers.scrape_grades.assert_not_called()
