"""Get the submission form for assignment 52541 directly."""
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

        # Go to assignment page
        page = await ctx.new_page()
        assign_url = f"{BASE_URL}/mod/assign/view.php?id=52541"
        print(f"Loading: {assign_url}")
        await page.goto(assign_url, wait_until="domcontentloaded", timeout=20_000)
        await page.wait_for_timeout(1_500)

        # Find the Add submission button/link
        add_btn = await page.query_selector(
            'a:has-text("Add submission"), '
            'button:has-text("Add submission"), '
            'a[href*="editsubmission"]'
        )

        if add_btn:
            href = await add_btn.get_attribute("href") or ""
            print(f"Add submission href: {href!r}")

            # Click it and follow
            async with page.expect_navigation():
                await add_btn.click()
            await page.wait_for_timeout(2_000)
            print(f"Submission form URL: {page.url}")

            html = await page.content()
            Path("submission_form.html").write_text(html, encoding="utf-8")
            await page.screenshot(path="submission_form.png", full_page=True)
            print(f"HTML saved ({len(html)} chars)")

            # Analyze form
            print("\n--- Form analysis ---")
            forms = await page.query_selector_all("form")
            for form in forms:
                action = await form.get_attribute("action") or ""
                method = await form.get_attribute("method") or ""
                if action:
                    print(f"Form: action={action!r} method={method!r}")

            # All inputs
            inputs = await page.query_selector_all("input")
            print(f"\nInputs ({len(inputs)}):")
            for inp in inputs:
                t = await inp.get_attribute("type") or "text"
                n = await inp.get_attribute("name") or ""
                v = (await inp.get_attribute("value") or "")[:40]
                if n:
                    print(f"  {t}: name={n!r} value={v!r}")

            # Textareas
            textareas = await page.query_selector_all("textarea")
            print(f"\nTextareas ({len(textareas)}):")
            for ta in textareas:
                n = await ta.get_attribute("name") or ""
                print(f"  name={n!r}")

            # File manager / upload area
            file_mgr = await page.query_selector(".filemanager, [data-fieldtype='filemanager']")
            if file_mgr:
                print("\nFile manager found!")
                fm_html = await file_mgr.inner_html()
                print(f"  {fm_html[:300]}")

            # Check for online text editor
            editor = await page.query_selector('.editor_atto_content, [contenteditable="true"]')
            if editor:
                print("\nOnline text editor found!")

            # Submit buttons
            submit_btns = await page.query_selector_all('input[type="submit"], button[type="submit"]')
            print(f"\nSubmit buttons ({len(submit_btns)}):")
            for btn in submit_btns:
                val = await btn.get_attribute("value") or (await btn.inner_text()).strip()
                print(f"  {val!r}")

        else:
            print("No 'Add submission' button found")
            html = await page.content()
            # Look for any submission-related links
            links = await page.query_selector_all("a")
            for link in links:
                text = (await link.inner_text()).strip()
                href = await link.get_attribute("href") or ""
                if "submit" in text.lower() or "submission" in text.lower():
                    print(f"  Link: {text!r} → {href}")

        await page.close()
        await browser.close()


asyncio.run(main())
