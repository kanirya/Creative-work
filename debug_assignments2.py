"""Debug assignments in the client context."""
import asyncio
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

    print("Loading course 10673...")
    await page.goto(f"{BASE_URL}/course/view.php?id=10673", wait_until="domcontentloaded", timeout=20_000)
    await page.wait_for_timeout(1_000)
    print(f"URL: {page.url}")
    print(f"Title: {await page.title()}")

    # Check if redirected to login
    if "login" in page.url or "microsoftonline" in page.url:
        print("SESSION EXPIRED - redirected to login!")
        await auth.close()
        return

    links = await page.query_selector_all('a[href*="/mod/assign/view.php"]')
    print(f"Assignment links: {len(links)}")
    for link in links:
        href = await link.get_attribute("href") or ""
        text = (await link.inner_text()).strip()
        name = text.split("\n")[0].strip()
        print(f"  name={name!r} href={href}")

    await page.close()
    await auth.close()


asyncio.run(test())
