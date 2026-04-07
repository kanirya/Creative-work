"""
Refresh the LMS session — handles Microsoft login with MFA.
Uses keyboard Enter for form submission (more reliable than button clicks).
"""
import asyncio
import json
from pathlib import Path


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
            locale="en-US",
        )
        await ctx.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )
        page = await ctx.new_page()

        print("Step 1: Navigate to LMS OIDC...")
        await page.goto(
            "https://lms.iqra.edu.pk/auth/oidc/?source=loginpage",
            wait_until="domcontentloaded", timeout=30_000
        )
        await asyncio.sleep(2)

        print("Step 2: Enter email + press Enter...")
        await page.wait_for_selector('input[name="loginfmt"]', timeout=15_000)
        await page.fill('input[name="loginfmt"]', "muhammad.141510.isb@iqra.edu.pk")
        await asyncio.sleep(0.6)
        await page.keyboard.press("Enter")
        await asyncio.sleep(4)
        print(f"  URL: {page.url[:80]}")

        print("Step 3: Enter password + press Enter...")
        await page.wait_for_selector('input[name="passwd"]', timeout=15_000)
        await page.fill('input[name="passwd"]', "Bree@4u4u")
        await asyncio.sleep(0.6)
        await page.keyboard.press("Enter")

        # Wait for the page to fully load after password
        print("  Waiting for post-password page...")
        await asyncio.sleep(6)
        print(f"  URL: {page.url[:80]}")
        title = await page.title()
        print(f"  Title: {title!r}")
        await page.screenshot(path="post_password.png")

        # Now poll for MFA, KMSI, or LMS redirect
        print("\nPolling for next step (MFA/KMSI/LMS)...")
        mfa_approved = False

        for i in range(120):
            await asyncio.sleep(1)
            url = page.url

            # Check if we reached LMS
            if "lms.iqra.edu.pk" in url and "microsoftonline" not in url:
                print(f"  ✓ Reached LMS after {i+1}s!")
                mfa_approved = True
                break

            # Check for KMSI
            if "kmsi" in url:
                print(f"  KMSI page after {i+1}s")
                kmsi = await page.query_selector('#idBtn_Back')
                if kmsi:
                    await kmsi.click()
                    await asyncio.sleep(3)
                mfa_approved = True
                break

            # Check for MFA number
            mfa_number = None
            for sel in ['[data-testid="displaySign"]', '#idRichContext_DisplaySign',
                        '.display-sign', '#idDiv_SAOTCAS_TD2', '[aria-label*="number"]']:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        text = (await el.inner_text()).strip()
                        if text and text.isdigit():
                            mfa_number = text
                            break
                except Exception:
                    pass

            if mfa_number:
                print(f"\n{'='*50}")
                print(f"  MFA NUMBER: {mfa_number}")
                print(f"  Enter {mfa_number} in Microsoft Authenticator NOW!")
                print(f"{'='*50}\n")

                # Wait for MFA approval
                for j in range(90):
                    await asyncio.sleep(1)
                    try:
                        cur = page.url
                        if "lms.iqra.edu.pk" in cur or "kmsi" in cur:
                            print(f"  ✓ MFA approved after {j+1}s!")
                            mfa_approved = True
                            break
                        still = await page.query_selector('[data-testid="displaySign"], #idRichContext_DisplaySign')
                        if not still:
                            print(f"  ✓ MFA element gone after {j+1}s, URL: {cur[:60]}")
                            mfa_approved = True
                            break
                    except Exception:
                        pass

                if mfa_approved:
                    await asyncio.sleep(3)
                    # Handle KMSI if it appears
                    try:
                        kmsi = await page.query_selector('#idBtn_Back')
                        if kmsi:
                            print("  Clicking No on KMSI...")
                            await kmsi.click()
                            await asyncio.sleep(3)
                    except Exception:
                        pass
                break

            # Every 10s print status
            if i % 10 == 9:
                print(f"  [{i+1}s] Still waiting... URL: {url[:60]}")
                await page.screenshot(path=f"wait_{i+1}.png")

        # Final check
        final_url = page.url
        print(f"\nFinal URL: {final_url[:80]}")

        if "lms.iqra.edu.pk" in final_url and "microsoftonline" not in final_url:
            state = await ctx.storage_state()
            Path("lms_session_test.json").write_text(json.dumps(state))
            print("✓ Session saved to lms_session_test.json")

            p2 = await ctx.new_page()
            await p2.goto("https://lms.iqra.edu.pk/user/profile.php",
                          wait_until="domcontentloaded", timeout=20_000)
            name_el = await p2.query_selector("h1")
            if name_el:
                print(f"✓ Logged in as: {(await name_el.inner_text()).strip()}")
            await p2.close()
            print("\n✓ Done! Now run: python start_lms_scraper.py")
        else:
            print(f"✗ Login did not complete. URL: {final_url[:80]}")
            print("  Check post_password.png for details")

        await browser.close()


asyncio.run(main())
