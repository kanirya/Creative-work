"""Debug why the service returns 0 assignments — save screenshot of what it sees."""
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "services/lms-scraper")

os.environ["MS_EMAIL"] = "muhammad.141510.isb@iqra.edu.pk"
os.environ["MS_PASSWORD"] = "Bree@4u4u"
os.environ["SESSION_STORAGE_PATH"] = str(Path("lms_session_test.json").absolute())
os.environ["LMS_BASE_URL"] = "https://lms.iqra.edu.pk"
os.environ["API_GATEWAY_URL"] = "http://localhost:5000"
os.environ["DATABASE_URL"] = "postgresql://edupilot:password@localhost:5432/edupilot"
os.environ["OPENAI_API_KEY"] = "sk-placeholder"
os.environ["EMBEDDING_MODEL"] = "text-embedding-3-small"

BASE_URL = "https://lms.iqra.edu.pk"


async def test():
    from app.services.lms_auth import get_lms_auth_service

    auth = get_lms_auth_service()
    ctx = await auth.get_authenticated_context()

    page = await ctx.new_page()
    try:
        url = f"{BASE_URL}/course/view.php?id=10673"
        print(f"Loading: {url}")
        await page.goto(url, wait_until="networkidle", timeout=30_000)
        await page.wait_for_timeout(2_000)

        print(f"URL after load: {page.url}")
        print(f"Title: {await page.title()}")

        # Save screenshot
        await page.screenshot(path="service_course_page.png", full_page=True)
        print("Screenshot saved: service_course_page.png")

        # Save HTML
        html = await page.content()
        Path("service_course_page.html").write_text(html, encoding="utf-8")
        print(f"HTML saved ({len(html)} chars)")

        # Check for assignment links
        links = await page.query_selector_all('a[href*="/mod/assign/view.php"]')
        print(f"Assignment links: {len(links)}")
        for link in links:
            href = await link.get_attribute("href") or ""
            text = (await link.inner_text()).strip()[:60]
            print(f"  {text!r} -> {href}")

        # Check if logged in
        user_menu = await page.query_selector('.usermenu, [data-region="user-menu"]')
        print(f"User menu found: {user_menu is not None}")

        # Check for any activities
        activities = await page.query_selector_all("li.activity")
        print(f"Activity items: {len(activities)}")

    finally:
        await page.close()
        await auth.close()


asyncio.run(test())
