"""Debug the actual courses page to find correct selectors."""
import asyncio
import json
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

        print("Loading courses page...")
        await page.goto(f"{BASE_URL}/my/courses.php", wait_until="networkidle", timeout=30_000)
        await page.wait_for_timeout(3_000)
        print(f"URL: {page.url}")
        print(f"Title: {await page.title()}")

        # Save HTML
        html = await page.content()
        Path("courses_page.html").write_text(html, encoding="utf-8")
        print(f"HTML saved ({len(html)} chars)")

        # Screenshot
        await page.screenshot(path="courses_page.png", full_page=True)
        print("Screenshot: courses_page.png")

        # Try selectors
        selectors = [
            'a[href*="/course/view.php?id="]',
            '.coursename a',
            'h3.coursename a',
            '.card-title a',
            '.course-info-container a',
            '[data-region="course-item"] a',
            '.coursebox a.aalink',
            'a.aalink',
            '.course-card a',
            '.course-list a',
            'li.course a',
        ]

        print("\nSelectors:")
        for sel in selectors:
            els = await page.query_selector_all(sel)
            if els:
                print(f"  ✓ {sel!r} → {len(els)}")
                for el in els[:3]:
                    text = (await el.inner_text()).strip()[:60]
                    href = (await el.get_attribute("href") or "")[:80]
                    print(f"      {text!r} → {href!r}")

        # All links with course in href
        all_links = await page.query_selector_all("a")
        course_links = []
        for link in all_links:
            href = await link.get_attribute("href") or ""
            if "course/view.php" in href:
                text = (await link.inner_text()).strip()
                course_links.append((href, text))

        print(f"\nAll course/view.php links: {len(course_links)}")
        for href, text in course_links[:10]:
            print(f"  {text!r} → {href}")

        await browser.close()


asyncio.run(main())
