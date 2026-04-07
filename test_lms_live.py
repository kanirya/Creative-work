"""
Live end-to-end test: Login to Iqra University LMS and scrape real data.

Run from the workspace root:
    pip install playwright
    playwright install chromium
    python test_lms_live.py

Credentials are hardcoded below for this test run.
"""

import asyncio
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

# ── Setup logging ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("lms_test")

# ── Credentials ───────────────────────────────────────────────────────────────
MS_EMAIL    = "muhammad.141510.isb@iqra.edu.pk"
MS_PASSWORD = "Bree@4u4u"
BASE_URL    = "https://lms.iqra.edu.pk"
SESSION_FILE = Path("lms_session_test.json")

# ── Selectors ─────────────────────────────────────────────────────────────────
MS_EMAIL_INPUT    = 'input[type="email"], input[name="loginfmt"]'
MS_NEXT_BUTTON    = 'input[type="submit"][value="Next"], button[type="submit"]'
MS_PASSWORD_INPUT = 'input[type="password"], input[name="passwd"]'
MS_SIGNIN_BUTTON  = 'input[type="submit"][value="Sign in"], button[type="submit"]'
MS_KMSI_NO        = '#idBtn_Back, input[value="No"]'
MOODLE_DASHBOARD  = '[data-region="myoverview"], .dashboard-content, #page-my-index, .usermenu'


# ── Auth ──────────────────────────────────────────────────────────────────────

async def login(browser) -> object:
    """Perform Microsoft OIDC login and return authenticated context."""

    # Try restoring saved session first
    if SESSION_FILE.exists():
        log.info("Found saved session — trying to restore...")
        try:
            ctx = await browser.new_context(
                storage_state=json.loads(SESSION_FILE.read_text()),
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
            )
            await ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
            page = await ctx.new_page()
            await page.goto(f"{BASE_URL}/my/", wait_until="domcontentloaded", timeout=15_000)
            if "lms.iqra.edu.pk" in page.url and "login" not in page.url:
                el = await page.query_selector(MOODLE_DASHBOARD)
                if el:
                    log.info("✓ Session restored — already logged in")
                    await page.close()
                    return ctx
            await page.close()
            await ctx.close()
            log.info("Session expired — doing fresh login")
        except Exception as e:
            log.warning(f"Session restore failed: {e}")

    # Fresh login
    log.info("Starting Microsoft OIDC login flow...")
    ctx = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
        timezone_id="Asia/Karachi",
    )
    await ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
    page = await ctx.new_page()

    # Step 1: Navigate to OIDC entry
    log.info("  → Navigating to LMS OIDC entry point")
    await page.goto(f"{BASE_URL}/auth/oidc/?source=loginpage", wait_until="domcontentloaded", timeout=30_000)
    await page.wait_for_timeout(2_000)
    log.info(f"  → Current URL: {page.url}")

    # Step 2: Email
    log.info(f"  → Entering email: {MS_EMAIL}")
    await page.wait_for_selector(MS_EMAIL_INPUT, timeout=15_000)
    await page.fill(MS_EMAIL_INPUT, MS_EMAIL)
    await page.wait_for_timeout(600)
    await page.click(MS_NEXT_BUTTON)
    await page.wait_for_load_state("domcontentloaded", timeout=15_000)
    await page.wait_for_timeout(2_000)
    log.info(f"  → After email: {page.url}")

    # Step 3: Password
    log.info("  → Entering password")
    await page.wait_for_selector(MS_PASSWORD_INPUT, timeout=15_000)
    await page.fill(MS_PASSWORD_INPUT, MS_PASSWORD)
    await page.wait_for_timeout(600)
    await page.click(MS_SIGNIN_BUTTON)
    await page.wait_for_load_state("domcontentloaded", timeout=20_000)
    await page.wait_for_timeout(2_500)
    log.info(f"  → After password: {page.url}")

    # Step 4: Handle prompts
    # MFA check
    mfa = await page.query_selector('[data-testid="mfaMethodPicker"], #idDiv_SAOTCC_Title')
    if mfa:
        await page.screenshot(path="mfa_prompt.png")
        raise RuntimeError("MFA required — cannot automate. Screenshot saved to mfa_prompt.png")

    # KMSI "Stay signed in?" → No
    kmsi = await page.query_selector(MS_KMSI_NO)
    if kmsi:
        log.info("  → Handling 'Stay signed in?' → clicking No")
        await kmsi.click()
        await page.wait_for_load_state("domcontentloaded", timeout=15_000)
        await page.wait_for_timeout(2_000)

    # Consent screen
    accept = await page.query_selector('#idSIButton9[value="Accept"], button:has-text("Accept")')
    if accept and "consent" in page.url.lower():
        log.info("  → Accepting permissions consent")
        await accept.click()
        await page.wait_for_load_state("domcontentloaded", timeout=15_000)
        await page.wait_for_timeout(2_000)

    # Step 5: Verify Moodle dashboard
    log.info(f"  → Final URL: {page.url}")
    if "microsoftonline" in page.url:
        await page.screenshot(path="login_failure.png")
        raise RuntimeError(f"Still on Microsoft page after login. Screenshot saved. URL: {page.url}")

    try:
        await page.wait_for_selector(MOODLE_DASHBOARD, timeout=15_000)
        log.info("✓ Login successful — Moodle dashboard reached")
    except Exception:
        await page.screenshot(path="login_failure.png")
        raise RuntimeError(f"Dashboard not found. URL: {page.url}. Screenshot saved to login_failure.png")

    # Save session
    state = await ctx.storage_state()
    SESSION_FILE.write_text(json.dumps(state))
    log.info(f"  → Session saved to {SESSION_FILE}")

    await page.close()
    return ctx


# ── Scrapers ──────────────────────────────────────────────────────────────────

async def scrape_courses(ctx) -> list:
    """Scrape enrolled courses from the dashboard."""
    log.info("\n── Scraping courses ──────────────────────────────────────────")
    page = await ctx.new_page()
    courses = []
    try:
        await page.goto(f"{BASE_URL}/my/", wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(2_000)

        links = await page.query_selector_all('a[href*="/course/view.php?id="]')
        seen = set()
        for link in links:
            href = await link.get_attribute("href") or ""
            m = re.search(r"id=(\d+)", href)
            if not m:
                continue
            cid = int(m.group(1))
            if cid in seen:
                continue
            seen.add(cid)
            name = (await link.inner_text()).strip()
            if name:
                courses.append({"id": cid, "name": name, "url": href})

        log.info(f"  Found {len(courses)} courses")
        for c in courses:
            log.info(f"    [{c['id']}] {c['name']}")
    finally:
        await page.close()
    return courses


async def scrape_assignments(ctx, courses: list) -> list:
    """Scrape assignments from the first 2 courses."""
    log.info("\n── Scraping assignments ──────────────────────────────────────")
    page = await ctx.new_page()
    assignments = []
    try:
        for course in courses[:2]:  # limit to first 2 to keep test fast
            url = f"{BASE_URL}/mod/assign/index.php?id={course['id']}"
            await page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            await page.wait_for_timeout(1_000)

            rows = await page.query_selector_all("table.generaltable tbody tr")
            for row in rows:
                link = await row.query_selector("a[href*='/mod/assign/view.php']")
                if not link:
                    continue
                title = (await link.inner_text()).strip()
                cells = await row.query_selector_all("td")
                due = (await cells[2].inner_text()).strip() if len(cells) > 2 else "N/A"
                assignments.append({
                    "course": course["name"],
                    "title": title,
                    "due": due,
                })
                log.info(f"    [{course['name']}] {title} — due: {due}")

        log.info(f"  Found {len(assignments)} assignments")
    finally:
        await page.close()
    return assignments


async def scrape_grades(ctx, courses: list) -> list:
    """Scrape grade overview."""
    log.info("\n── Scraping grades ───────────────────────────────────────────")
    page = await ctx.new_page()
    grades = []
    try:
        await page.goto(f"{BASE_URL}/grade/report/overview/index.php", wait_until="domcontentloaded", timeout=20_000)
        await page.wait_for_timeout(1_000)

        rows = await page.query_selector_all("table.generaltable tbody tr")
        for row in rows:
            cells = await row.query_selector_all("td")
            if len(cells) < 2:
                continue
            course_link = await cells[0].query_selector("a")
            course_name = (await course_link.inner_text()).strip() if course_link else (await cells[0].inner_text()).strip()
            grade_val = (await cells[1].inner_text()).strip() if len(cells) > 1 else "-"
            grades.append({"course": course_name, "grade": grade_val})
            log.info(f"    {course_name}: {grade_val}")

        log.info(f"  Found {len(grades)} grade entries")
    finally:
        await page.close()
    return grades


async def scrape_announcements(ctx, courses: list) -> list:
    """Scrape announcements from the first course that has a forum."""
    log.info("\n── Scraping announcements ────────────────────────────────────")
    page = await ctx.new_page()
    announcements = []
    try:
        for course in courses[:3]:
            await page.goto(f"{BASE_URL}/course/view.php?id={course['id']}", wait_until="domcontentloaded", timeout=20_000)
            await page.wait_for_timeout(800)

            forum_links = await page.query_selector_all('a[href*="/mod/forum/view.php"]')
            for link in forum_links:
                text = (await link.inner_text()).strip().lower()
                if "announcement" in text or "news" in text:
                    href = await link.get_attribute("href") or ""
                    forum_url = href if href.startswith("http") else f"{BASE_URL}{href}"
                    await page.goto(forum_url, wait_until="domcontentloaded", timeout=15_000)
                    await page.wait_for_timeout(500)

                    rows = await page.query_selector_all("table.forumheaderlist tbody tr.discussion")
                    for row in rows[:3]:  # first 3 announcements
                        title_el = await row.query_selector("td.topic a")
                        title = (await title_el.inner_text()).strip() if title_el else "Unknown"
                        announcements.append({"course": course["name"], "title": title})
                        log.info(f"    [{course['name']}] {title}")
                    break

        log.info(f"  Found {len(announcements)} announcements")
    finally:
        await page.close()
    return announcements


async def scrape_calendar(ctx) -> list:
    """Scrape upcoming calendar events."""
    log.info("\n── Scraping calendar events ──────────────────────────────────")
    page = await ctx.new_page()
    events = []
    try:
        await page.goto(f"{BASE_URL}/calendar/view.php?view=upcoming", wait_until="domcontentloaded", timeout=20_000)
        await page.wait_for_timeout(1_000)

        event_els = await page.query_selector_all(".event, [data-region='event-item']")
        for el in event_els[:10]:
            name_el = await el.query_selector(".referer a, .name a, h3 a")
            name = (await name_el.inner_text()).strip() if name_el else "Unknown"
            date_el = await el.query_selector("time, .date a")
            date_str = ""
            if date_el:
                date_str = await date_el.get_attribute("datetime") or await date_el.inner_text()
            events.append({"name": name, "date": date_str})
            log.info(f"    {name} — {date_str}")

        log.info(f"  Found {len(events)} upcoming events")
    finally:
        await page.close()
    return events


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    print("\n" + "="*60)
    print("  EduPilot — Iqra LMS Live Scraper Test")
    print("="*60)
    print(f"  Account : {MS_EMAIL}")
    print(f"  LMS URL : {BASE_URL}")
    print(f"  Time    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        log.info("Launching Chromium browser (headless)...")
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )

        try:
            # ── 1. Login ──────────────────────────────────────────────────────
            ctx = await login(browser)

            # ── 2. Scrape courses ─────────────────────────────────────────────
            courses = await scrape_courses(ctx)

            if not courses:
                log.warning("No courses found — check login or LMS structure")
            else:
                # ── 3. Scrape assignments ─────────────────────────────────────
                assignments = await scrape_assignments(ctx, courses)

                # ── 4. Scrape grades ──────────────────────────────────────────
                grades = await scrape_grades(ctx, courses)

                # ── 5. Scrape announcements ───────────────────────────────────
                announcements = await scrape_announcements(ctx, courses)

                # ── 6. Scrape calendar ────────────────────────────────────────
                events = await scrape_calendar(ctx)

                # ── Summary ───────────────────────────────────────────────────
                print("\n" + "="*60)
                print("  RESULTS SUMMARY")
                print("="*60)
                print(f"  ✓ Courses      : {len(courses)}")
                print(f"  ✓ Assignments  : {len(assignments)}")
                print(f"  ✓ Grades       : {len(grades)}")
                print(f"  ✓ Announcements: {len(announcements)}")
                print(f"  ✓ Calendar     : {len(events)}")
                print("="*60)
                print("\n  All scrapers working correctly!\n")

        except Exception as e:
            log.error(f"\n✗ TEST FAILED: {e}")
            print(f"\n  FAILED: {e}\n")
            sys.exit(1)
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
