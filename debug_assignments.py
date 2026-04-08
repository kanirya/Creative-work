"""Debug why assignments return 0."""
import asyncio, json
from pathlib import Path

SESSION_FILE = Path("lms_session_test.json")
BASE_URL = "https://lms.iqra.edu.pk"

async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await browser.new_context(
            storage_state=json.loads(SESSION_FILE.read_text()),
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = await ctx.new_page()

        # Navigate to course 10673
        print("Loading course page...")
        await page.goto(f"{BASE_URL}/course/view.php?id=10673", wait_until="domcontentloaded", timeout=20_000)
        await page.wait_for_timeout(1_000)
        print(f"URL: {page.url}")
        print(f"Title: {await page.title()}")

        # Find assignment links
        links = await page.query_selector_all('a[href*="/mod/assign/view.php"]')
        print(f"Assignment links found: {len(links)}")
        for link in links:
            href = await link.get_attribute("href") or ""
            text = (await link.inner_text()).strip()[:60]
            print(f"  {text!r} -> {href}")

        await browser.close()

asyncio.run(main())
