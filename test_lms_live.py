"""
Live end-to-end test: Login to Iqra University LMS and scrape real data.
Handles Microsoft Authenticator number-matching MFA prompt.

Run:
    python test_lms_live.py
"""

import asyncio
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("lms_test")

MS_EMAIL     = "muhammad.141510.isb@iqra.edu.pk"
MS_PASSWORD  = "Bree@4u4u"
BASE_URL     = "https://lms.iqra.edu.pk"
SESSION_FILE = Path("lms_session_test.json")

MOODLE_DASHBOARD = (
    '[data-region="myoverview"], .dashboard-content, '
    '#page-my-index, #page-site-index, .usermenu'
)


async def login(browser):
    """Full Microsoft OIDC login with MFA number-match support."""

    # Try restoring saved session
    if SESSION_FILE.exists():
        log.info("Found saved session — trying to restore...")
        try:
            ctx = await browser.new_context(
                storage_state=json.loads(SESSION_FILE.read_text()),
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
            )
            await ctx.add_init_script(
                "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
            )
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

    log.info("Starting Microsoft OIDC login flow...")
    ctx = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
        timezone_id="Asia/Karachi",
    )
    await ctx.add_init_script(
        "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
    )
    page = await ctx.new_page()

    # Step 1: OIDC entry
    log.info("  → Navigating to LMS OIDC entry point")
    await page.goto(
        f"{BASE_URL}/auth/oidc/?source=loginpage",
        wait_until="domcontentloaded",
        timeout=30_000,
    )
    await page.wait_for_timeout(2_000)

    # Step 2: Email
    log.info(f"  → Entering email: {MS_EMAIL}")
    await page.wait_for_selector('input[name="loginfmt"]', timeout=15_000)
    await page.fill('input[name="loginfmt"]', MS_EMAIL)
    await page.wait_for_timeout(600)
    await page.click('input[type="submit"]')
    await page.wait_for_load_state("domcontentloaded", timeout=15_000)
    await page.wait_for_timeout(2_000)

    # Step 3: Password
    log.info("  → Entering password")
    await page.wait_for_selector('input[name="passwd"], input[type="password"]', timeout=15_000)
    await page.fill('input[name="passwd"], input[type="password"]', MS_PASSWORD)
    await page.wait_for_timeout(600)

    # Click Sign in
    submit = await page.query_selector('input[type="submit"][value="Sign in"]')
    if not submit:
        submit = await page.query_selector('input[type="submit"]')
    if not submit:
        submit = await page.query_selector('button[type="submit"]')
    if submit:
        await submit.click()
    await page.wait_for_load_state("domcontentloaded", timeout=20_000)
    await page.wait_for_timeout(2_500)
    log.info(f"  → URL after password: {page.url}")

    # Step 4: Handle MFA — Microsoft Authenticator number matching
    # The page shows a 2-digit number; user enters it in the Authenticator app
    mfa_number = None
    for selector in [
        '[data-testid="displaySign"]',
        '.display-sign',
        '#idRichContext_DisplaySign',
        'div[aria-label*="number"]',
        '.number-display',
    ]:
        el = await page.query_selector(selector)
        if el:
            mfa_number = (await el.inner_text()).strip()
            break

    # Also try to find any large number displayed on the page
    if not mfa_number:
        # Look for the number in page text
        content = await page.content()
        # Microsoft shows the number in a specific div
        match = re.search(r'<[^>]*class="[^"]*display[^"]*"[^>]*>\s*(\d{2})\s*<', content)
        if match:
            mfa_number = match.group(1)

    if mfa_number:
        log.info(f"\n{'='*50}")
        log.info(f"  MFA REQUIRED — Number Matching")
        log.info(f"  Enter this number in your Authenticator app: {mfa_number}")
        log.info(f"{'='*50}")
        print(f"\n  *** Open Microsoft Authenticator and enter: {mfa_number} ***\n")
        await page.screenshot(path="mfa_screen.png")
        log.info("  Screenshot saved to mfa_screen.png")
        log.info("  Waiting up to 60 seconds for you to approve...")

        # Wait for MFA approval — poll until we leave the MFA page
        approved = False
        for i in range(60):
            await asyncio.sleep(1)
            current_url = page.url
            if "microsoftonline" not in current_url or "kmsi" in current_url or "lms.iqra.edu.pk" in current_url:
                approved = True
                log.info(f"  ✓ MFA approved after {i+1}s")
                break
            # Check if still on MFA page
            still_mfa = await page.query_selector('[data-testid="displaySign"], #idRichContext_DisplaySign')
            if not still_mfa:
                approved = True
                log.info(f"  ✓ MFA page left after {i+1}s")
                break

        if not approved:
            await page.screenshot(path="mfa_timeout.png")
            raise RuntimeError("MFA approval timed out after 60 seconds")

        await page.wait_for_load_state("domcontentloaded", timeout=15_000)
        await page.wait_for_timeout(2_000)
        log.info(f"  → URL after MFA: {page.url}")

    else:
        # Check if it's a different MFA type
        mfa_generic = await page.query_selector(
            '#idDiv_SAOTCC_Title, [data-testid="mfaMethodPicker"], '
            '#idDiv_SAOTCAS_Title, .tile-img'
        )
        if mfa_generic:
            await page.screenshot(path="mfa_unknown.png")
            log.warning("  Unknown MFA prompt detected — screenshot saved to mfa_unknown.png")
            log.info("  Waiting 30s for manual approval...")
            await asyncio.sleep(30)

    # Step 5: KMSI "Stay signed in?" → No
    await page.wait_for_timeout(1_000)
    kmsi = await page.query_selector('#idBtn_Back, input[value="No"]')
    if kmsi:
        log.info("  → Handling 'Stay signed in?' → clicking No")
        await kmsi.click()
        await page.wait_for_load_state("domcontentloaded", timeout=15_000)
        await page.wait_for_timeout(2_000)

    # Step 6: Verify Moodle dashboard
    log.info(f"  → Final URL: {page.url}")
    if "microsoftonline" in page.url:
        await page.screenshot(path="login_failure.png")
        raise RuntimeError(
            f"Still on Microsoft page. URL: {page.url}\nScreenshot: login_failure.png"
        )

    try:
        await page.wait_for_selector(MOODLE_DASHBOARD, timeout=15_000)
        log.info("✓ Login successful — Moodle dashboard reached")
    except Exception:
        await page.screenshot(path="login_failure.png")
        raise RuntimeError(
            f"Dashboard not found. URL: {page.url}\nScreenshot: login_failure.png"
        )

    # Save session
    state = await ctx.storage_state()
    SESSION_FILE.write_text(json.dumps(state))
    log.info(f"  → Session saved to {SESSION_FILE}")

    await page.close()
    return ctx


async def scrape_courses(ctx):
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

        log.info(f"  Found {len(courses)} courses:")
        for c in courses:
            log.info(f"    [{c['id']}] {c['name']}")
    finally:
        await page.close()
    return courses


async def scrape_assignments(ctx, courses):
    log.info("\n── Scraping assignments ──────────────────────────────────────")
    page = await ctx.new_page()
    assignments = []
    try:
        for course in courses[:3]:
            url = f"{BASE_URL}/mod/assign/index.php?id={course['id']}"
            await page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            await page.wait_for_timeout(800)

            rows = await page.query_selector_all("table.generaltable tbody tr")
            for row in rows:
                link = await row.query_selector("a[href*='/mod/assign/view.php']")
                if not link:
                    continue
                title = (await link.inner_text()).strip()
                cells = await row.query_selector_all("td")
                due = (await cells[2].inner_text()).strip() if len(cells) > 2 else "N/A"
                assignments.append({"course": course["name"], "title": title, "due": due})
                log.info(f"    [{course['name']}] {title} — due: {due}")

        log.info(f"  Total: {len(assignments)} assignments")
    finally:
        await page.close()
    return assignments


async def scrape_grades(ctx, courses):
    log.info("\n── Scraping grades ───────────────────────────────────────────")
    page = await ctx.new_page()
    grades = []
    try:
        await page.goto(
            f"{BASE_URL}/grade/report/overview/index.php",
            wait_until="domcontentloaded",
            timeout=20_000,
        )
        await page.wait_for_timeout(1_000)

        rows = await page.query_selector_all("table.generaltable tbody tr")
        for row in rows:
            cells = await row.query_selector_all("td")
            if len(cells) < 2:
                continue
            link = await cells[0].query_selector("a")
            name = (await link.inner_text()).strip() if link else (await cells[0].inner_text()).strip()
            grade = (await cells[1].inner_text()).strip()
            grades.append({"course": name, "grade": grade})
            log.info(f"    {name}: {grade}")

        log.info(f"  Total: {len(grades)} grade entries")
    finally:
        await page.close()
    return grades


async def scrape_announcements(ctx, courses):
    log.info("\n── Scraping announcements ────────────────────────────────────")
    page = await ctx.new_page()
    announcements = []
    try:
        for course in courses[:3]:
            await page.goto(
                f"{BASE_URL}/course/view.php?id={course['id']}",
                wait_until="domcontentloaded",
                timeout=20_000,
            )
            await page.wait_for_timeout(600)

            forum_links = await page.query_selector_all('a[href*="/mod/forum/view.php"]')
            for link in forum_links:
                text = (await link.inner_text()).strip().lower()
                if "announcement" in text or "news" in text:
                    href = await link.get_attribute("href") or ""
                    forum_url = href if href.startswith("http") else f"{BASE_URL}{href}"
                    await page.goto(forum_url, wait_until="domcontentloaded", timeout=15_000)
                    await page.wait_for_timeout(500)

                    rows = await page.query_selector_all(
                        "table.forumheaderlist tbody tr.discussion"
                    )
                    for row in rows[:3]:
                        title_el = await row.query_selector("td.topic a")
                        title = (await title_el.inner_text()).strip() if title_el else "Unknown"
                        announcements.append({"course": course["name"], "title": title})
                        log.info(f"    [{course['name']}] {title}")
                    break

        log.info(f"  Total: {len(announcements)} announcements")
    finally:
        await page.close()
    return announcements


async def scrape_calendar(ctx):
    log.info("\n── Scraping calendar events ──────────────────────────────────")
    page = await ctx.new_page()
    events = []
    try:
        await page.goto(
            f"{BASE_URL}/calendar/view.php?view=upcoming",
            wait_until="domcontentloaded",
            timeout=20_000,
        )
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

        log.info(f"  Total: {len(events)} upcoming events")
    finally:
        await page.close()
    return events


async def main():
    print("\n" + "=" * 60)
    print("  EduPilot — Iqra LMS Live Scraper Test")
    print("=" * 60)
    print(f"  Account : {MS_EMAIL}")
    print(f"  LMS URL : {BASE_URL}")
    print(f"  Time    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

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
            ctx = await login(browser)

            courses = await scrape_courses(ctx)

            if not courses:
                log.warning("No courses found — check login or LMS structure")
                return

            assignments  = await scrape_assignments(ctx, courses)
            grades       = await scrape_grades(ctx, courses)
            announcements = await scrape_announcements(ctx, courses)
            events       = await scrape_calendar(ctx)

            print("\n" + "=" * 60)
            print("  RESULTS SUMMARY")
            print("=" * 60)
            print(f"  ✓ Courses       : {len(courses)}")
            print(f"  ✓ Assignments   : {len(assignments)}")
            print(f"  ✓ Grades        : {len(grades)}")
            print(f"  ✓ Announcements : {len(announcements)}")
            print(f"  ✓ Calendar      : {len(events)}")
            print("=" * 60)

            if courses:
                print("\n  Sample courses:")
                for c in courses[:5]:
                    print(f"    • {c['name']}")

            if grades:
                print("\n  Sample grades:")
                for g in grades[:5]:
                    print(f"    • {g['course']}: {g['grade']}")

            print("\n  ✓ Scraper is working correctly!\n")

        except Exception as e:
            log.error(f"TEST FAILED: {e}")
            print(f"\n  FAILED: {e}\n")
            sys.exit(1)
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
