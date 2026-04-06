"""
Iqra University LMS Authentication via Microsoft Azure AD OIDC.

The LMS uses Moodle's Microsoft 365 OIDC plugin. Authentication flow:
  1. Navigate to https://lms.iqra.edu.pk/auth/oidc/?source=loginpage
  2. Microsoft login page: enter email → Next
  3. Microsoft login page: enter password → Sign in
  4. Handle "Stay signed in?" → click No
  5. Redirected back to https://lms.iqra.edu.pk/my/ (Moodle dashboard)
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    async_playwright,
)

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Selectors ────────────────────────────────────────────────────────────────

# Microsoft login page selectors
MS_EMAIL_INPUT = 'input[type="email"], input[name="loginfmt"]'
MS_NEXT_BUTTON = 'input[type="submit"][value="Next"], button[type="submit"]'
MS_PASSWORD_INPUT = 'input[type="password"], input[name="passwd"]'
MS_SIGNIN_BUTTON = 'input[type="submit"][value="Sign in"], button[type="submit"]'
MS_KMSI_NO = '#idBtn_Back, input[value="No"]'          # "Stay signed in? → No"
MS_KMSI_YES = '#idSIButton9, input[value="Yes"]'       # "Stay signed in? → Yes"

# Moodle dashboard selectors (confirm successful login)
MOODLE_DASHBOARD = (
    '[data-region="myoverview"], '
    '.dashboard-content, '
    '#page-my-index, '
    '#page-site-index, '
    '.usermenu'
)

# ── Exceptions ────────────────────────────────────────────────────────────────


class LMSAuthenticationError(Exception):
    """Raised when LMS / Microsoft authentication fails."""


class MFARequiredError(LMSAuthenticationError):
    """Raised when Microsoft requires MFA that cannot be automated."""


class PasswordChangeRequiredError(LMSAuthenticationError):
    """Raised when Microsoft requires a password change."""


# ── Auth Service ──────────────────────────────────────────────────────────────


class LMSAuthService:
    """
    Authenticates with Iqra LMS via Microsoft Azure AD OIDC using Playwright.

    Usage:
        service = LMSAuthService()
        context = await service.get_authenticated_context()
        # use context to create pages and scrape data
        await service.close()
    """

    LMS_OIDC_URL = "https://lms.iqra.edu.pk/auth/oidc/?source=loginpage"
    LMS_BASE_URL = "https://lms.iqra.edu.pk"

    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._session_path = Path(settings.session_storage_path)

    # ── Public API ────────────────────────────────────────────────────────────

    async def get_authenticated_context(self) -> BrowserContext:
        """
        Return an authenticated Moodle browser context.
        Tries to restore a saved session first; falls back to full login.
        """
        await self._ensure_browser()

        if await self._try_restore_session():
            logger.info("Restored existing Moodle session from disk")
            return self._context

        logger.info("No valid session found — performing full Microsoft OIDC login")
        await self._full_login()
        return self._context

    async def close(self):
        """Close browser and release resources."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Browser closed")

    # ── Browser setup ─────────────────────────────────────────────────────────

    async def _ensure_browser(self):
        if self._browser is not None:
            return
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )
        logger.info("Chromium browser launched")

    async def _new_context(self) -> BrowserContext:
        """Create a new browser context with realistic browser fingerprint."""
        context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="Asia/Karachi",
        )
        # Hide webdriver flag to avoid bot detection
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        return context

    # ── Session persistence ───────────────────────────────────────────────────

    async def _try_restore_session(self) -> bool:
        """
        Attempt to restore a previously saved browser session.
        Returns True if session is valid, False otherwise.
        """
        if not self._session_path.exists():
            return False

        try:
            with open(self._session_path) as f:
                storage_state = json.load(f)

            self._context = await self._browser.new_context(
                storage_state=storage_state,
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
            )
            await self._context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            if await self._is_session_valid():
                return True

            # Session expired — close and fall through to full login
            await self._context.close()
            self._context = None
            logger.info("Saved session has expired")
            return False

        except Exception as e:
            logger.warning(f"Failed to restore session: {e}")
            if self._context:
                await self._context.close()
                self._context = None
            return False

    async def _is_session_valid(self) -> bool:
        """Check if the current context has a valid Moodle session."""
        page = await self._context.new_page()
        try:
            await page.goto(
                f"{self.LMS_BASE_URL}/my/",
                wait_until="domcontentloaded",
                timeout=15_000,
            )
            # If we're redirected to login, session is invalid
            if "login" in page.url or "microsoftonline" in page.url:
                return False
            # Check for dashboard element
            el = await page.query_selector(MOODLE_DASHBOARD)
            return el is not None
        except Exception as e:
            logger.debug(f"Session validation error: {e}")
            return False
        finally:
            await page.close()

    async def _save_session(self):
        """Persist browser cookies/storage to disk for reuse."""
        try:
            self._session_path.parent.mkdir(parents=True, exist_ok=True)
            storage_state = await self._context.storage_state()
            with open(self._session_path, "w") as f:
                json.dump(storage_state, f)
            logger.info(f"Session saved to {self._session_path}")
        except Exception as e:
            logger.warning(f"Failed to save session: {e}")

    # ── Full Microsoft OIDC login ─────────────────────────────────────────────

    async def _full_login(self):
        """
        Perform the full Microsoft OIDC login flow:
          1. Navigate to Moodle OIDC entry point
          2. Fill Microsoft email → Next
          3. Fill Microsoft password → Sign in
          4. Handle "Stay signed in?" → No
          5. Verify Moodle dashboard is reached
          6. Save session to disk
        """
        ms_email = settings.ms_email
        ms_password = settings.ms_password

        if not ms_email or not ms_password:
            raise LMSAuthenticationError(
                "MS_EMAIL and MS_PASSWORD environment variables must be set"
            )

        self._context = await self._new_context()
        page = await self._context.new_page()

        try:
            # ── Step 1: Navigate to OIDC entry point ──────────────────────────
            logger.info("Navigating to Moodle OIDC entry point")
            await page.goto(self.LMS_OIDC_URL, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_timeout(1_500)  # let Microsoft page settle

            # ── Step 2: Enter email ───────────────────────────────────────────
            logger.info(f"Entering Microsoft email: {ms_email}")
            await page.wait_for_selector(MS_EMAIL_INPUT, timeout=15_000)
            await page.fill(MS_EMAIL_INPUT, ms_email)
            await page.wait_for_timeout(500)
            await page.click(MS_NEXT_BUTTON)
            await page.wait_for_load_state("domcontentloaded", timeout=15_000)
            await page.wait_for_timeout(1_500)

            # ── Step 3: Enter password ────────────────────────────────────────
            logger.info("Entering Microsoft password")
            await page.wait_for_selector(MS_PASSWORD_INPUT, timeout=15_000)
            await page.fill(MS_PASSWORD_INPUT, ms_password)
            await page.wait_for_timeout(500)
            await page.click(MS_SIGNIN_BUTTON)
            await page.wait_for_load_state("domcontentloaded", timeout=20_000)
            await page.wait_for_timeout(2_000)

            # ── Step 4: Handle post-login prompts ─────────────────────────────
            await self._handle_post_login_prompts(page)

            # ── Step 5: Verify we reached Moodle ─────────────────────────────
            await self._verify_moodle_login(page)

            # ── Step 6: Save session ──────────────────────────────────────────
            await self._save_session()
            logger.info("Microsoft OIDC login successful")

        except (LMSAuthenticationError, MFARequiredError, PasswordChangeRequiredError):
            raise
        except Exception as e:
            # Capture screenshot for debugging
            try:
                screenshot_path = "/tmp/login_failure.png"
                await page.screenshot(path=screenshot_path)
                logger.error(f"Login failure screenshot saved to {screenshot_path}")
            except Exception:
                pass
            raise LMSAuthenticationError(f"Login failed: {e}") from e
        finally:
            await page.close()

    async def _handle_post_login_prompts(self, page: Page):
        """Handle various Microsoft post-login prompts."""
        current_url = page.url

        # Check for MFA prompt
        if await page.query_selector('[data-testid="mfaMethodPicker"], #idDiv_SAOTCC_Title'):
            raise MFARequiredError(
                "Microsoft requires MFA. Use a service account without MFA for automated scraping."
            )

        # Check for password change prompt
        if await page.query_selector('#ForceSignIn, [data-testid="passwordChangeRequired"]'):
            raise PasswordChangeRequiredError(
                "Microsoft requires a password change. Please update the password and try again."
            )

        # Handle "Stay signed in?" (KMSI) prompt
        kmsi_no = await page.query_selector(MS_KMSI_NO)
        if kmsi_no:
            logger.info("Handling 'Stay signed in?' prompt → clicking No")
            await kmsi_no.click()
            await page.wait_for_load_state("domcontentloaded", timeout=15_000)
            await page.wait_for_timeout(2_000)

        # Handle permissions consent screen
        accept_btn = await page.query_selector('#idSIButton9[value="Accept"], button:has-text("Accept")')
        if accept_btn and "consent" in page.url.lower():
            logger.info("Handling permissions consent screen → clicking Accept")
            await accept_btn.click()
            await page.wait_for_load_state("domcontentloaded", timeout=15_000)
            await page.wait_for_timeout(2_000)

    async def _verify_moodle_login(self, page: Page):
        """Verify that we successfully reached the Moodle dashboard."""
        # Wait for redirect back to Moodle
        try:
            await page.wait_for_url(
                lambda url: "lms.iqra.edu.pk" in url and "microsoftonline" not in url,
                timeout=20_000,
            )
        except Exception:
            raise LMSAuthenticationError(
                f"Did not redirect back to Moodle. Current URL: {page.url}"
            )

        # Wait for dashboard to load
        try:
            await page.wait_for_selector(MOODLE_DASHBOARD, timeout=15_000)
        except Exception:
            raise LMSAuthenticationError(
                f"Moodle dashboard not found after login. Current URL: {page.url}"
            )

        logger.info(f"Successfully reached Moodle dashboard: {page.url}")


# ── Singleton ─────────────────────────────────────────────────────────────────

_instance: Optional[LMSAuthService] = None


def get_lms_auth_service() -> LMSAuthService:
    """Return the singleton LMSAuthService instance."""
    global _instance
    if _instance is None:
        _instance = LMSAuthService()
    return _instance
