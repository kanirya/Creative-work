"""Check what the login failure screenshot shows."""
import asyncio
import json
import sys
from pathlib import Path

SESSION_FILE = Path("lms_session_test.json")


async def main():
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        await ctx.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )

        # Step through login manually with verbose output
        page = await ctx.new_page()

        print("Step 1: Navigate to OIDC")
        await page.goto("https://lms.iqra.edu.pk/auth/oidc/?source=loginpage",
                        wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(2_000)
        print(f"  URL: {page.url}")

        print("Step 2: Email")
        await page.wait_for_selector('input[name="loginfmt"]', timeout=15_000)
        await page.fill('input[name="loginfmt"]', "muhammad.141510.isb@iqra.edu.pk")
        await page.wait_for_timeout(600)
        await page.click('input[type="submit"]')
        await page.wait_for_load_state("domcontentloaded", timeout=15_000)
        await page.wait_for_timeout(2_000)
        print(f"  URL after email: {page.url}")

        print("Step 3: Password")
        await page.wait_for_selector('input[name="passwd"]', timeout=15_000)
        await page.fill('input[name="passwd"]', "Bree@4u4u")
        await page.wait_for_timeout(600)
        submit = await page.query_selector('input[type="submit"][value="Sign in"]')
        if not submit:
            submit = await page.query_selector('input[type="submit"]')
        await submit.click()
        await page.wait_for_load_state("domcontentloaded", timeout=20_000)
        await page.wait_for_timeout(2_500)
        print(f"  URL after password: {page.url}")

        # Check for MFA
        for sel in ['[data-testid="displaySign"]', '#idRichContext_DisplaySign', '.display-sign']:
            el = await page.query_selector(sel)
            if el:
                num = (await el.inner_text()).strip()
                print(f"\n  *** MFA NUMBER: {num} ***")
                print(f"  Enter {num} in your Authenticator app now!")
                print("  Waiting 60 seconds...")

                for i in range(60):
                    await asyncio.sleep(1)
                    if "microsoftonline" not in page.url or "kmsi" in page.url or "lms.iqra.edu.pk" in page.url:
                        print(f"  MFA approved after {i+1}s!")
                        break
                    still = await page.query_selector(sel)
                    if not still:
                        print(f"  MFA page left after {i+1}s!")
                        break
                break

        await page.wait_for_load_state("domcontentloaded", timeout=15_000)
        await page.wait_for_timeout(2_000)
        print(f"  URL after MFA: {page.url}")

        # KMSI
        kmsi = await page.query_selector('#idBtn_Back, input[value="No"]')
        if kmsi:
            print("  Clicking 'No' on Stay signed in")
            await kmsi.click()
            await page.wait_for_load_state("domcontentloaded", timeout=15_000)
            await page.wait_for_timeout(2_000)

        print(f"  Final URL: {page.url}")
        await page.screenshot(path="final_state.png")

        if "lms.iqra.edu.pk" in page.url and "microsoftonline" not in page.url:
            print("\n  ✓ LOGIN SUCCESSFUL!")
            # Save session
            state = await ctx.storage_state()
            Path("lms_session_test.json").write_text(json.dumps(state))
            print("  Session saved to lms_session_test.json")

            # Test profile
            profile_page = await ctx.new_page()
            await profile_page.goto("https://lms.iqra.edu.pk/user/profile.php",
                                    wait_until="domcontentloaded", timeout=20_000)
            name_el = await profile_page.query_selector("h1")
            if name_el:
                print(f"  Student: {(await name_el.inner_text()).strip()}")
            await profile_page.close()
        else:
            print(f"\n  ✗ Login failed. URL: {page.url}")

        await browser.close()


asyncio.run(main())
