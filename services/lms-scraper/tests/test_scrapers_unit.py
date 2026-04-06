"""
Unit tests for Moodle scrapers using mocked Playwright pages.
These tests do NOT require real LMS credentials.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.scrapers import MoodleScrapers, parse_moodle_date
from app.models import CourseData


# ── Date parsing tests ────────────────────────────────────────────────────────

class TestParseMoodleDate:
    def test_full_format(self):
        result = parse_moodle_date("Sunday, 15 December 2024, 11:59 PM")
        assert result is not None
        assert result.day == 15
        assert result.month == 12
        assert result.year == 2024
        assert result.hour == 23
        assert result.minute == 59

    def test_short_format(self):
        result = parse_moodle_date("15 December 2024")
        assert result is not None
        assert result.day == 15
        assert result.month == 12

    def test_iso_format(self):
        result = parse_moodle_date("2024-12-15T23:59:00+00:00")
        assert result is not None
        assert result.day == 15

    def test_empty_string(self):
        assert parse_moodle_date("") is None

    def test_none_like_string(self):
        assert parse_moodle_date("   ") is None

    def test_invalid_format(self):
        assert parse_moodle_date("not a date") is None


# ── Course code extraction ────────────────────────────────────────────────────

class TestExtractCourseCode:
    def test_standard_code(self):
        code = MoodleScrapers._extract_course_code("CS-301: Data Structures")
        assert code == "CS-301"

    def test_no_code(self):
        code = MoodleScrapers._extract_course_code("Introduction to Programming")
        assert code == "Introduction to Prog"  # truncated to 20 chars

    def test_four_digit_code(self):
        code = MoodleScrapers._extract_course_code("MGT-4501 Strategic Management")
        assert code == "MGT-4501"


# ── Scraper unit tests with mocked context ────────────────────────────────────

def make_mock_element(text: str = "", href: str = "") -> AsyncMock:
    el = AsyncMock()
    el.inner_text = AsyncMock(return_value=text)
    el.get_attribute = AsyncMock(return_value=href)
    el.query_selector = AsyncMock(return_value=None)
    return el


@pytest.mark.asyncio
async def test_scrape_courses_extracts_course_ids():
    """Test that course IDs are correctly extracted from href attributes."""
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    mock_page.goto = AsyncMock()
    mock_page.wait_for_timeout = AsyncMock()
    mock_page.close = AsyncMock()

    # Two course links
    link1 = make_mock_element("CS-301: Data Structures", "/course/view.php?id=123")
    link2 = make_mock_element("MGT-401: Management", "/course/view.php?id=456")
    mock_page.query_selector_all = AsyncMock(return_value=[link1, link2])

    # Mock _enrich_course to return course as-is
    scrapers = MoodleScrapers(mock_context)
    scrapers._enrich_course = AsyncMock(side_effect=lambda page, c: c)

    courses = await scrapers.scrape_courses()

    assert len(courses) == 2
    assert courses[0].course_id == 123
    assert courses[1].course_id == 456
    assert courses[0].course_name == "CS-301: Data Structures"


@pytest.mark.asyncio
async def test_scrape_courses_deduplicates():
    """Test that duplicate course IDs are not returned."""
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    mock_page.goto = AsyncMock()
    mock_page.wait_for_timeout = AsyncMock()
    mock_page.close = AsyncMock()

    # Same course ID twice
    link1 = make_mock_element("CS-301", "/course/view.php?id=123")
    link2 = make_mock_element("CS-301 (duplicate)", "/course/view.php?id=123")
    mock_page.query_selector_all = AsyncMock(return_value=[link1, link2])

    scrapers = MoodleScrapers(mock_context)
    scrapers._enrich_course = AsyncMock(side_effect=lambda page, c: c)

    courses = await scrapers.scrape_courses()
    assert len(courses) == 1


@pytest.mark.asyncio
async def test_scrape_courses_handles_empty_page():
    """Test graceful handling when no courses are found."""
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    mock_page.goto = AsyncMock()
    mock_page.wait_for_timeout = AsyncMock()
    mock_page.close = AsyncMock()
    mock_page.query_selector_all = AsyncMock(return_value=[])

    scrapers = MoodleScrapers(mock_context)
    courses = await scrapers.scrape_courses()
    assert courses == []


@pytest.mark.asyncio
async def test_scrape_assignments_handles_no_courses():
    """Test that scraping assignments with empty course list returns empty list."""
    mock_context = AsyncMock()
    scrapers = MoodleScrapers(mock_context)
    result = await scrapers.scrape_assignments([])
    assert result == []
