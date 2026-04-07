"""Debug: inspect the Moodle dashboard HTML to find course selectors."""
import asyncio
import json
import re
from pathlib import Path

SESSION_FILE = Path("lms_session_test.json")
BASE_URL = "https://lms.iqra.edu.pk"


async def main():
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        ctx = await browser.new_context(
            storage_state=json.loads(SESSION_FILE.read_text()),
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        await ctx.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )
        page = await ctx.new_page()

        print("Loading dashboard...")
        await page.goto(f"{BASE_URL}/my/", wait_until="networkidle", timeout=30_000)
        await page.wait_for_timeout(3_000)
        print(f"URL: {page.url}")

        # Save full HTML
        html = await page.content()
        Path("dashboard_debug.html").write_text(html, encoding="utf-8")
        print(f"Full HTML saved to dashboard_debug.html ({len(html)} chars)")

        # Screenshot
        await page.screenshot(path="dashboard_debug.png", full_page=True)
        print("Screenshot saved to dashboard_debug.png")

        # Try various course selectors
        selectors_to_try = [
            'a[href*="/course/view.php?id="]',
            '[data-region="course-item"]',
            '[data-courseid]',
            '.coursebox',
            '.course-info-container',
            '.course-name',
            '.coursename a',
            'h3.coursename a',
            '.card-title a',
            '[data-region="myoverview"] a',
            '.courses-view a',
            '.course-list-item a',
            'li.course-listitem a',
        ]

        print("\nTrying course selectors:")
        for sel in selectors_to_try:
            els = await page.query_selector_all(sel)
            if els:
                print(f"  ✓ '{sel}' → {len(els)} elements")
                for el in els[:3]:
                    try:
                        text = (await el.inner_text()).strip()[:60]
                        href = await el.get_attribute("href") or ""
                        print(f"      text={text!r} href={href[:60]!r}")
                    except Exception:
                        pass
            else:
                print(f"  ✗ '{sel}' → 0")

        # Also check all links containing "course"
        print("\nAll links containing 'course/view.php':")
        all_links = await page.query_selector_all("a")
        course_links = []
        for link in all_links:
            href = await link.get_attribute("href") or ""
            if "course/view.php" in href:
                text = (await link.inner_text()).strip()
                course_links.append((href, text))

        print(f"  Found {len(course_links)} course links")
        for href, text in course_links[:10]:
            print(f"    {text!r} → {href}")

        # Check page title and main content
        title = await page.title()
        print(f"\nPage title: {title!r}")

        # Check if there's a "My courses" section
        my_courses = await page.query_selector_all('[aria-label*="course"], [title*="course"]')
        print(f"Elements with course aria-label/title: {len(my_courses)}")

        await browser.close()


asyncio.run(main())
