"""
Full LMS Explorer — maps every section of Iqra LMS.
Saves HTML of each page and prints all selectors found.
Run: python explore_lms_full.py
"""
import asyncio
import json
import re
from pathlib import Path

SESSION_FILE = Path("lms_session_test.json")
BASE_URL = "https://lms.iqra.edu.pk"
OUT = Path("lms_explore")
OUT.mkdir(exist_ok=True)


async def get_page(ctx, url, name, wait="networkidle"):
    page = await ctx.new_page()
    try:
        await page.goto(url, wait_until=wait, timeout=30_000)
        await page.wait_for_timeout(2_000)
        html = await page.content()
        (OUT / f"{name}.html").write_text(html, encoding="utf-8")
        await page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
        print(f"  ✓ {name}: {url} ({len(html)} chars)")
        return page, html
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        await page.close()
        return None, ""


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

        print("\n=== STEP 1: Get courses ===")
        page, html = await get_page(ctx, f"{BASE_URL}/my/courses.php", "courses")
        if not page:
            print("Session expired — re-run test_lms_live.py first")
            return

        # Extract course IDs
        courses = []
        seen = set()
        links = await page.query_selector_all('a[href*="/course/view.php?id="]')
        for link in links:
            href = await link.get_attribute("href") or ""
            m = re.search(r"id=(\d+)", href)
            if not m:
                continue
            cid = int(m.group(1))
            if cid in seen:
                continue
            seen.add(cid)
            raw = (await link.inner_text()).strip()
            name = raw.split("\n")[0].strip()
            if name and name.lower() != "course name":
                courses.append({"id": cid, "name": name})
                print(f"    Course [{cid}]: {name}")
        await page.close()

        print(f"\n  Found {len(courses)} courses")

        # Use first course for deep exploration
        if not courses:
            print("No courses found!")
            return

        c = courses[0]
        cid = c["id"]
        cname = c["name"]
        print(f"\n=== STEP 2: Explore course [{cid}] {cname} ===")

        # Course main page
        page, html = await get_page(ctx, f"{BASE_URL}/course/view.php?id={cid}", f"course_{cid}")
        if page:
            # Find all activity types
            activities = await page.query_selector_all("li.activity")
            print(f"  Activities found: {len(activities)}")
            for act in activities[:20]:
                cls = await act.get_attribute("class") or ""
                link = await act.query_selector("a")
                if link:
                    href = await link.get_attribute("href") or ""
                    text = (await link.inner_text()).strip().split("\n")[0][:60]
                    print(f"    {cls.split()[-1] if cls else 'unknown'}: {text!r} → {href[:80]}")
            await page.close()

        print(f"\n=== STEP 3: Assignments for course {cid} ===")
        page, html = await get_page(ctx, f"{BASE_URL}/mod/assign/index.php?id={cid}", f"assignments_{cid}")
        if page:
            rows = await page.query_selector_all("table.generaltable tbody tr")
            print(f"  Assignment rows: {len(rows)}")
            assign_urls = []
            for row in rows:
                link = await row.query_selector("a[href*='/mod/assign/view.php']")
                if not link:
                    continue
                title = (await link.inner_text()).strip()
                href = await link.get_attribute("href") or ""
                cells = await row.query_selector_all("td")
                due = (await cells[2].inner_text()).strip() if len(cells) > 2 else ""
                status = (await cells[3].inner_text()).strip() if len(cells) > 3 else ""
                print(f"    {title!r} due={due!r} status={status!r}")
                assign_urls.append(href)
            await page.close()

            # Explore first assignment detail
            if assign_urls:
                print(f"\n=== STEP 4: Assignment detail ===")
                page, html = await get_page(ctx, assign_urls[0], "assignment_detail")
                if page:
                    # Check submission form
                    forms = await page.query_selector_all("form")
                    print(f"  Forms: {len(forms)}")
                    for form in forms:
                        action = await form.get_attribute("action") or ""
                        print(f"    form action={action!r}")

                    # Check file upload
                    file_inputs = await page.query_selector_all('input[type="file"]')
                    print(f"  File inputs: {len(file_inputs)}")

                    # Check text submission
                    textareas = await page.query_selector_all("textarea")
                    print(f"  Textareas: {len(textareas)}")

                    # Check submission button
                    btns = await page.query_selector_all('button, input[type="submit"]')
                    for btn in btns:
                        txt = (await btn.inner_text()).strip() if await btn.inner_text() else await btn.get_attribute("value") or ""
                        print(f"  Button: {txt!r}")

                    # Check submission status
                    status_table = await page.query_selector("table.generaltable")
                    if status_table:
                        rows = await status_table.query_selector_all("tr")
                        print(f"\n  Submission status table:")
                        for row in rows:
                            cells = await row.query_selector_all("td, th")
                            if len(cells) >= 2:
                                label = (await cells[0].inner_text()).strip()
                                value = (await cells[1].inner_text()).strip()
                                print(f"    {label}: {value}")
                    await page.close()

        print(f"\n=== STEP 5: Grades overview ===")
        page, html = await get_page(ctx, f"{BASE_URL}/grade/report/overview/index.php", "grades_overview")
        if page:
            rows = await page.query_selector_all("table.generaltable tbody tr")
            print(f"  Grade rows: {len(rows)}")
            for row in rows[:10]:
                cells = await row.query_selector_all("td")
                if len(cells) >= 2:
                    name_el = await cells[0].query_selector("a")
                    name = (await name_el.inner_text()).strip() if name_el else (await cells[0].inner_text()).strip()
                    grade = (await cells[1].inner_text()).strip()
                    if name:
                        print(f"    {name}: {grade}")
            await page.close()

        print(f"\n=== STEP 6: Detailed grades for course {cid} ===")
        page, html = await get_page(ctx, f"{BASE_URL}/grade/report/user/index.php?id={cid}", f"grades_detail_{cid}")
        if page:
            rows = await page.query_selector_all("table tr")
            print(f"  Grade detail rows: {len(rows)}")
            for row in rows[:15]:
                cells = await row.query_selector_all("td, th")
                if len(cells) >= 2:
                    item = (await cells[0].inner_text()).strip()[:50]
                    grade = (await cells[1].inner_text()).strip()
                    if item:
                        print(f"    {item}: {grade}")
            await page.close()

        print(f"\n=== STEP 7: Calendar / upcoming events ===")
        page, html = await get_page(ctx, f"{BASE_URL}/calendar/view.php?view=upcoming", "calendar_upcoming")
        if page:
            # Try different event selectors
            for sel in [".event", "[data-region='event-item']", ".calendar-event-panel", "li.event"]:
                els = await page.query_selector_all(sel)
                if els:
                    print(f"  Selector {sel!r}: {len(els)} events")
                    for el in els[:5]:
                        text = (await el.inner_text()).strip()[:80]
                        print(f"    {text!r}")
                    break

            # Also check for event links
            event_links = await page.query_selector_all("a[href*='calendar']")
            print(f"  Calendar links: {len(event_links)}")
            await page.close()

        print(f"\n=== STEP 8: Forums / Announcements for course {cid} ===")
        page, html = await get_page(ctx, f"{BASE_URL}/course/view.php?id={cid}", f"course_forums_{cid}")
        if page:
            forum_links = await page.query_selector_all('a[href*="/mod/forum/view.php"]')
            print(f"  Forum links: {len(forum_links)}")
            for link in forum_links:
                text = (await link.inner_text()).strip()
                href = await link.get_attribute("href") or ""
                print(f"    {text!r} → {href}")

            # Navigate to first forum
            if forum_links:
                href = await forum_links[0].get_attribute("href") or ""
                forum_url = href if href.startswith("http") else f"{BASE_URL}{href}"
                await page.close()

                page, html = await get_page(ctx, forum_url, f"forum_{cid}")
                if page:
                    discussions = await page.query_selector_all("table.forumheaderlist tbody tr.discussion")
                    print(f"  Forum discussions: {len(discussions)}")
                    for disc in discussions[:5]:
                        title_el = await disc.query_selector("td.topic a")
                        title = (await title_el.inner_text()).strip() if title_el else "?"
                        print(f"    {title!r}")
                    await page.close()
            else:
                await page.close()

        print(f"\n=== STEP 9: Quiz activities for course {cid} ===")
        page, html = await get_page(ctx, f"{BASE_URL}/course/view.php?id={cid}", f"course_quizzes_{cid}")
        if page:
            quiz_links = await page.query_selector_all('a[href*="/mod/quiz/view.php"]')
            print(f"  Quiz links: {len(quiz_links)}")
            for link in quiz_links[:5]:
                text = (await link.inner_text()).strip()
                href = await link.get_attribute("href") or ""
                print(f"    {text!r} → {href}")

            if quiz_links:
                href = await quiz_links[0].get_attribute("href") or ""
                quiz_url = href if href.startswith("http") else f"{BASE_URL}{href}"
                await page.close()

                page, html = await get_page(ctx, quiz_url, f"quiz_detail_{cid}")
                if page:
                    rows = await page.query_selector_all("table.generaltable tr")
                    print(f"  Quiz detail rows: {len(rows)}")
                    for row in rows[:10]:
                        cells = await row.query_selector_all("td, th")
                        if len(cells) >= 2:
                            label = (await cells[0].inner_text()).strip()
                            value = (await cells[1].inner_text()).strip()
                            if label:
                                print(f"    {label}: {value}")
                    await page.close()
            else:
                await page.close()

        print(f"\n=== STEP 10: User profile ===")
        page, html = await get_page(ctx, f"{BASE_URL}/user/profile.php", "user_profile")
        if page:
            name_el = await page.query_selector("h1, .page-header-headings h1")
            if name_el:
                print(f"  Student name: {(await name_el.inner_text()).strip()}")
            email_el = await page.query_selector('[href^="mailto:"]')
            if email_el:
                print(f"  Email: {(await email_el.inner_text()).strip()}")
            await page.close()

        print(f"\n=== STEP 11: Check assignment submission (upload) ===")
        # Find an assignment with submission enabled
        page, html = await get_page(ctx, f"{BASE_URL}/mod/assign/index.php?id={cid}", f"assign_check_{cid}")
        if page:
            links = await page.query_selector_all("a[href*='/mod/assign/view.php']")
            for link in links:
                href = await link.get_attribute("href") or ""
                assign_page = await ctx.new_page()
                try:
                    await assign_page.goto(href, wait_until="domcontentloaded", timeout=20_000)
                    await assign_page.wait_for_timeout(1_000)

                    # Check for "Add submission" or "Edit submission" button
                    submit_btn = await assign_page.query_selector(
                        'a[href*="action=editsubmission"], '
                        'button:has-text("Add submission"), '
                        'a:has-text("Add submission"), '
                        'a:has-text("Edit submission")'
                    )
                    if submit_btn:
                        btn_text = (await submit_btn.inner_text()).strip()
                        btn_href = await submit_btn.get_attribute("href") or ""
                        title_el = await assign_page.query_selector("h2, .page-header-headings h1")
                        title = (await title_el.inner_text()).strip() if title_el else "?"
                        print(f"  Assignment with submission: {title!r}")
                        print(f"    Button: {btn_text!r} → {btn_href}")

                        # Navigate to submission form
                        if btn_href:
                            sub_url = btn_href if btn_href.startswith("http") else f"{BASE_URL}{btn_href}"
                            sub_page = await ctx.new_page()
                            try:
                                await sub_page.goto(sub_url, wait_until="domcontentloaded", timeout=20_000)
                                await sub_page.wait_for_timeout(1_000)
                                sub_html = await sub_page.content()
                                (OUT / "submission_form.html").write_text(sub_html, encoding="utf-8")
                                await sub_page.screenshot(path=str(OUT / "submission_form.png"))

                                # Check form elements
                                file_inputs = await sub_page.query_selector_all('input[type="file"]')
                                textareas = await sub_page.query_selector_all("textarea")
                                print(f"    File inputs: {len(file_inputs)}")
                                print(f"    Textareas: {len(textareas)}")

                                # Check for online text editor
                                editor = await sub_page.query_selector('.editor_atto, .atto_editable, [contenteditable]')
                                print(f"    Rich text editor: {editor is not None}")

                                forms = await sub_page.query_selector_all("form")
                                for form in forms:
                                    action = await form.get_attribute("action") or ""
                                    method = await form.get_attribute("method") or ""
                                    print(f"    Form: action={action!r} method={method!r}")

                                print("    Submission form HTML saved to lms_explore/submission_form.html")
                            finally:
                                await sub_page.close()
                        break
                finally:
                    await assign_page.close()
            await page.close()

        print(f"\n\n{'='*60}")
        print("EXPLORATION COMPLETE")
        print(f"All pages saved to: {OUT}/")
        print(f"{'='*60}\n")

        await browser.close()


asyncio.run(main())
