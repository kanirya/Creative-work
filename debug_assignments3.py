"""Trace exactly what get_assignments does."""
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

    # Replicate exactly what get_assignments does
    page = await ctx.new_page()
    try:
        course_id = 10673
        print(f"Navigating to course {course_id}...")
        await page.goto(
            f"{BASE_URL}/course/view.php?id={course_id}",
            wait_until="domcontentloaded",
            timeout=20_000,
        )
        await page.wait_for_timeout(1_000)
        print(f"URL: {page.url}")
        print(f"Title: {await page.title()}")

        if "login" in page.url or "microsoftonline" in page.url:
            print("SESSION EXPIRED!")
            return

        assign_links = await page.query_selector_all('a[href*="/mod/assign/view.php"]')
        print(f"Raw assignment links: {len(assign_links)}")

        seen = set()
        assignments = []
        for link in assign_links:
            href = await link.get_attribute("href") or ""
            import re
            m = re.search(r"id=(\d+)", href)
            if not m:
                print(f"  No ID in href: {href}")
                continue
            aid = int(m.group(1))
            if aid in seen:
                print(f"  Duplicate ID {aid}, skipping")
                continue
            seen.add(aid)
            raw = (await link.inner_text()).strip()
            name = raw.split("\n")[0].strip()
            print(f"  ID={aid} raw={raw!r} name={name!r}")
            if name:
                assignments.append({"id": aid, "name": name, "course_id": course_id})
            else:
                print(f"  SKIPPED (empty name)")

        print(f"\nFinal assignments: {len(assignments)}")
        for a in assignments:
            print(f"  {a}")

    finally:
        await page.close()
        await auth.close()


asyncio.run(test())
