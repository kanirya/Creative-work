"""Debug script to inspect Microsoft login page selectors."""
import asyncio
from playwright.async_api import async_playwright


async def debug():
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
        page = await ctx.new_page()

        print("Step 1: Navigate to OIDC entry point")
        await page.goto(
            "https://lms.iqra.edu.pk/auth/oidc/?source=loginpage",
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        await page.wait_for_timeout(2_000)
        print(f"  URL: {page.url}")

        print("\nStep 2: Fill email")
        await page.wait_for_selector('input[name="loginfmt"]', timeout=15_000)
        await page.fill('input[name="loginfmt"]', "muhammad.141510.isb@iqra.edu.pk")
        await page.wait_for_timeout(600)

        # Click Next button
        await page.click('input[type="submit"]')
        await page.wait_for_load_state("domcontentloaded", timeout=15_000)
        await page.wait_for_timeout(2_500)
        print(f"  URL after email: {page.url}")

        print("\nStep 3: Inspect password page")
        await page.screenshot(path="debug_password_page.png")
        print("  Screenshot: debug_password_page.png")

        # List all inputs
        inputs = await page.query_selector_all("input")
        print(f"  Inputs found: {len(inputs)}")
        for inp in inputs:
            t = await inp.get_attribute("type")
            n = await inp.get_attribute("name")
            v = await inp.get_attribute("value")
            vis = await inp.is_visible()
            print(f"    input: type={t!r} name={n!r} value={v!r} visible={vis}")

        # List all buttons
        buttons = await page.query_selector_all("button")
        print(f"  Buttons found: {len(buttons)}")
        for btn in buttons:
            t = await btn.get_attribute("type")
            txt = (await btn.inner_text()).strip()
            vis = await btn.is_visible()
            print(f"    button: type={t!r} text={txt!r} visible={vis}")

        print("\nStep 4: Fill password and submit")
        # Try filling password
        pwd_input = await page.query_selector('input[name="passwd"], input[type="password"]')
        if pwd_input:
            await pwd_input.fill("Bree@4u4u")
            await page.wait_for_timeout(600)
            print("  Password filled")

            # Try clicking submit
            submit = await page.query_selector('input[type="submit"][value="Sign in"], input[type="submit"]')
            if submit:
                val = await submit.get_attribute("value")
                print(f"  Clicking submit: value={val!r}")
                await submit.click()
            else:
                # Try button
                btn = await page.query_selector('button[type="submit"]')
                if btn:
                    txt = await btn.inner_text()
                    print(f"  Clicking button: {txt!r}")
                    await btn.click()

            await page.wait_for_load_state("domcontentloaded", timeout=20_000)
            await page.wait_for_timeout(3_000)
            print(f"  URL after password: {page.url}")
            await page.screenshot(path="debug_after_password.png")
            print("  Screenshot: debug_after_password.png")

            # Check for KMSI
            kmsi = await page.query_selector("#idBtn_Back")
            if kmsi:
                print("  KMSI prompt detected — clicking No")
                await kmsi.click()
                await page.wait_for_load_state("domcontentloaded", timeout=15_000)
                await page.wait_for_timeout(2_000)
                print(f"  URL after KMSI: {page.url}")

            await page.screenshot(path="debug_final.png")
            print(f"  Final URL: {page.url}")
            print("  Screenshot: debug_final.png")
        else:
            print("  ERROR: Password input not found!")
            html = await page.content()
            print(f"  Page HTML (first 2000 chars):\n{html[:2000]}")

        await browser.close()


asyncio.run(debug())
