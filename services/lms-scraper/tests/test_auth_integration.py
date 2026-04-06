"""
Integration tests for Iqra LMS Microsoft OIDC authentication.

These tests hit the real LMS and require valid credentials.
Run with: pytest -m integration --no-header -v

Set environment variables before running:
  MS_EMAIL=muhammad.141510.isb@iqra.edu.pk
  MS_PASSWORD=<password>
"""

import os
import pytest
import pytest_asyncio

# Skip all tests in this file if credentials are not set
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def credentials():
    email = os.getenv("MS_EMAIL", "")
    password = os.getenv("MS_PASSWORD", "")
    if not email or not password:
        pytest.skip("MS_EMAIL and MS_PASSWORD not set — skipping integration tests")
    return {"email": email, "password": password}


@pytest.mark.asyncio
async def test_microsoft_oidc_login(credentials):
    """Test full Microsoft OIDC login flow against real Iqra LMS."""
    from app.services.lms_auth import LMSAuthService

    service = LMSAuthService()
    try:
        context = await service.get_authenticated_context()

        # Verify MoodleSession cookie is present
        cookies = await context.cookies()
        cookie_names = [c["name"] for c in cookies]
        assert "MoodleSession" in cookie_names, (
            f"MoodleSession cookie not found. Got: {cookie_names}"
        )

        # Verify we can access the dashboard
        page = await context.new_page()
        await page.goto("https://lms.iqra.edu.pk/my/", wait_until="domcontentloaded")
        assert "microsoftonline" not in page.url, f"Still on Microsoft page: {page.url}"
        assert "lms.iqra.edu.pk" in page.url, f"Not on LMS: {page.url}"
        await page.close()

    finally:
        await service.close()


@pytest.mark.asyncio
async def test_session_persistence(credentials, tmp_path):
    """Test that session is saved and can be restored."""
    import json
    from app.services.lms_auth import LMSAuthService
    from app.config import get_settings

    session_file = tmp_path / "test_session.json"

    # Patch session path
    service = LMSAuthService()
    service._session_path = session_file

    try:
        # First login — should create session file
        await service.get_authenticated_context()
        assert session_file.exists(), "Session file was not created"

        session_data = json.loads(session_file.read_text())
        assert "cookies" in session_data, "Session file missing cookies"

        # Second call — should restore from file
        await service.close()
        service2 = LMSAuthService()
        service2._session_path = session_file
        await service2._ensure_browser()
        restored = await service2._try_restore_session()
        assert restored, "Session was not restored from file"

    finally:
        await service.close()


@pytest.mark.asyncio
async def test_scrape_courses(credentials):
    """Test that courses can be scraped after login."""
    from app.services.lms_auth import LMSAuthService
    from app.services.scrapers import MoodleScrapers

    service = LMSAuthService()
    try:
        context = await service.get_authenticated_context()
        scrapers = MoodleScrapers(context)
        courses = await scrapers.scrape_courses()

        assert len(courses) > 0, "No courses found — check login or LMS structure"
        for course in courses:
            assert course.course_id > 0
            assert course.course_name
            assert course.url.startswith("https://lms.iqra.edu.pk")

    finally:
        await service.close()


@pytest.mark.asyncio
async def test_scrape_assignments(credentials):
    """Test that assignments can be scraped for enrolled courses."""
    from app.services.lms_auth import LMSAuthService
    from app.services.scrapers import MoodleScrapers

    service = LMSAuthService()
    try:
        context = await service.get_authenticated_context()
        scrapers = MoodleScrapers(context)

        courses = await scrapers.scrape_courses()
        assert courses, "No courses to scrape assignments from"

        assignments = await scrapers.scrape_assignments(courses[:2])  # limit to 2 courses
        # Assignments may be empty if none exist, but should not raise
        for a in assignments:
            assert a.title
            assert a.course_id > 0

    finally:
        await service.close()


@pytest.mark.asyncio
async def test_scrape_grades(credentials):
    """Test that grades can be scraped."""
    from app.services.lms_auth import LMSAuthService
    from app.services.scrapers import MoodleScrapers

    service = LMSAuthService()
    try:
        context = await service.get_authenticated_context()
        scrapers = MoodleScrapers(context)

        courses = await scrapers.scrape_courses()
        grades = await scrapers.scrape_grades(courses[:2])

        for g in grades:
            assert g.course_name
            assert g.item_name

    finally:
        await service.close()
