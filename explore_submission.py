"""Explore assignment submission form in detail."""
import asyncio
import json
import re
from pathlib import Path

SESSION_FILE = Path("lms_session_test.json")
BASE_URL = "https://lms.iqra.edu.pk"
OUT = Path("lms_explore")


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

        # Known assignments from exploration
        assignments = [
            {"id": 52541, "name": "lecture 2 numerical slide 4 and 5", "course_id": 10673},
            {"id": 61349, "name": "Assignment # 1", "course_id": 10673},
        ]

        # Also check DATABASE SYSTEMS course for "Assignment 01 is due tomorrow"
        db_course_id = 10702

        print("=== Checking all assignments across all courses ===\n")

        all_courses = [10673, 10678, 10699, 10702, 10707, 11325, 10665]

        for cid in all_courses:
            page = await ctx.new_page()
            await page.goto(f"{BASE_URL}/course/view.php?id={cid}", wait_until="domcontentloaded", timeout=20_000)
            await page.wait_for_timeout(1_000)

            title_el = await page.query_selector("h1, .page-header-headings h1")
            course_title = (await title_el.inner_text()).strip() if title_el else f"Course {cid}"

            assign_links = await page.query_selector_all('a[href*="/mod/assign/view.php"]')
            print(f"Course [{cid}] {course_title[:50]}: {len(assign_links)} assignments")

            for link in assign_links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip().split("\n")[0][:60]
                if text and text.lower() not in ("", "assignment"):
                    print(f"  → {text!r}: {href}")
            await page.close()

        print("\n=== Checking assignment detail + submission form ===\n")

        # Check assignment 52541 (lecture 2 numerical)
        for assign_id in [52541, 61349]:
            page = await ctx.new_page()
            url = f"{BASE_URL}/mod/assign/view.php?id={assign_id}"
            await page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            await page.wait_for_timeout(1_500)

            title_el = await page.query_selector("h2, .page-header-headings h1")
            title = (await title_el.inner_text()).strip() if title_el else f"Assignment {assign_id}"
            print(f"Assignment [{assign_id}]: {title}")

            # Status table
            rows = await page.query_selector_all("table.generaltable tr")
            for row in rows:
                cells = await row.query_selector_all("td, th")
                if len(cells) >= 2:
                    label = (await cells[0].inner_text()).strip()
                    value = (await cells[1].inner_text()).strip()
                    if label:
                        print(f"  {label}: {value}")

            # Submission button
            add_btn = await page.query_selector(
                'a[href*="action=editsubmission"], '
                'a:has-text("Add submission"), '
                'a:has-text("Edit submission"), '
                'button:has-text("Add submission")'
            )
            if add_btn:
                btn_text = (await add_btn.inner_text()).strip()
                btn_href = await add_btn.get_attribute("href") or ""
                print(f"  Submission button: {btn_text!r}")

                if btn_href:
                    sub_url = btn_href if btn_href.startswith("http") else f"{BASE_URL}{btn_href}"
                    sub_page = await ctx.new_page()
                    await sub_page.goto(sub_url, wait_until="domcontentloaded", timeout=20_000)
                    await sub_page.wait_for_timeout(1_500)

                    html = await sub_page.content()
                    (OUT / f"submission_form_{assign_id}.html").write_text(html, encoding="utf-8")
                    await sub_page.screenshot(path=str(OUT / f"submission_form_{assign_id}.png"))

                    print(f"  Submission form URL: {sub_url}")

                    # Form details
                    forms = await sub_page.query_selector_all("form")
                    for form in forms:
                        action = await form.get_attribute("action") or ""
                        method = await form.get_attribute("method") or ""
                        if action:
                            print(f"  Form: action={action!r} method={method!r}")

                    # File upload
                    file_inputs = await sub_page.query_selector_all('input[type="file"]')
                    print(f"  File inputs: {len(file_inputs)}")
                    for fi in file_inputs:
                        name = await fi.get_attribute("name") or ""
                        accept = await fi.get_attribute("accept") or ""
                        print(f"    file input name={name!r} accept={accept!r}")

                    # Text areas
                    textareas = await sub_page.query_selector_all("textarea")
                    print(f"  Textareas: {len(textareas)}")
                    for ta in textareas:
                        name = await ta.get_attribute("name") or ""
                        print(f"    textarea name={name!r}")

                    # Hidden inputs (important for CSRF token)
                    hidden = await sub_page.query_selector_all('input[type="hidden"]')
                    print(f"  Hidden inputs: {len(hidden)}")
                    for h in hidden[:10]:
                        name = await h.get_attribute("name") or ""
                        value = await h.get_attribute("value") or ""
                        print(f"    hidden name={name!r} value={value[:30]!r}")

                    # Submit buttons
                    submit_btns = await sub_page.query_selector_all('input[type="submit"], button[type="submit"]')
                    for btn in submit_btns:
                        val = await btn.get_attribute("value") or await btn.inner_text()
                        print(f"  Submit button: {val!r}")

                    await sub_page.close()
            else:
                print("  No submission button found (already submitted or not open)")

            print()
            await page.close()

        print("=== Checking DATABASE SYSTEMS assignments (due tomorrow) ===\n")
        page = await ctx.new_page()
        await page.goto(f"{BASE_URL}/mod/assign/index.php?id={db_course_id}", wait_until="domcontentloaded", timeout=20_000)
        await page.wait_for_timeout(1_000)
        html = await page.content()
        (OUT / f"assignments_{db_course_id}.html").write_text(html, encoding="utf-8")

        rows = await page.query_selector_all("table.generaltable tbody tr")
        print(f"DB Systems assignments: {len(rows)} rows")
        for row in rows:
            link = await row.query_selector("a")
            if link:
                text = (await link.inner_text()).strip()
                href = await link.get_attribute("href") or ""
                cells = await row.query_selector_all("td")
                due = (await cells[2].inner_text()).strip() if len(cells) > 2 else ""
                print(f"  {text!r} due={due!r} → {href}")
        await page.close()

        await browser.close()
        print("\nDone. Check lms_explore/ for screenshots.")


asyncio.run(main())
