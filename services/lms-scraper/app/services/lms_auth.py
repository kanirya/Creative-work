from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from typing import Optional
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LMSAuthenticationError(Exception):
    """Raised when LMS authentication fails"""
    pass


class LMSAuthService:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
    
    async def initialize_browser(self):
        """Initialize Playwright browser"""
        if self.browser is None:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            logger.info("Browser initialized")
    
    async def close_browser(self):
        """Close browser and cleanup"""
        if self.context:
            await self.context.close()
            self.context = None
        if self.browser:
            await self.browser.close()
            self.browser = None
            logger.info("Browser closed")
    
    async def authenticate(self, username: str, password: str) -> BrowserContext:
        """
        Authenticate with LMS and return browser context
        
        Args:
            username: LMS username
            password: LMS password
        
        Returns:
            Authenticated browser context
        
        Raises:
            LMSAuthenticationError: If authentication fails
        """
        try:
            await self.initialize_browser()
            
            # Create new browser context
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = await self.context.new_page()
            
            logger.info(f"Navigating to LMS login page: {settings.lms_login_url}")
            await page.goto(settings.lms_login_url, timeout=settings.lms_timeout)
            
            # Wait for login form to load
            await page.wait_for_selector('input[name="username"], input[type="text"]', timeout=10000)
            
            # Fill in credentials
            logger.info(f"Filling credentials for user: {username}")
            await page.fill('input[name="username"], input[type="text"]', username)
            await page.fill('input[name="password"], input[type="password"]', password)
            
            # Click login button
            login_button_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign In")'
            ]
            
            login_clicked = False
            for selector in login_button_selectors:
                try:
                    await page.click(selector, timeout=2000)
                    login_clicked = True
                    logger.info(f"Clicked login button with selector: {selector}")
                    break
                except:
                    continue
            
            if not login_clicked:
                raise LMSAuthenticationError("Could not find login button")
            
            # Wait for navigation after login
            try:
                await page.wait_for_load_state('networkidle', timeout=15000)
            except:
                # Fallback: wait for URL change
                await page.wait_for_timeout(3000)
            
            # Check if login was successful
            current_url = page.url
            
            # Check for error messages
            error_selectors = [
                '.error',
                '.alert-danger',
                '[class*="error"]',
                'text=Invalid credentials',
                'text=Login failed'
            ]
            
            for selector in error_selectors:
                try:
                    error_element = await page.query_selector(selector)
                    if error_element:
                        error_text = await error_element.inner_text()
                        logger.error(f"Login error detected: {error_text}")
                        raise LMSAuthenticationError(f"Authentication failed: {error_text}")
                except:
                    continue
            
            # Verify we're logged in by checking for dashboard elements
            dashboard_selectors = [
                '[class*="dashboard"]',
                '[class*="home"]',
                'text=Dashboard',
                'text=My Courses',
                '.course-list'
            ]
            
            logged_in = False
            for selector in dashboard_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        logged_in = True
                        logger.info(f"Login verified with selector: {selector}")
                        break
                except:
                    continue
            
            if not logged_in and current_url == settings.lms_login_url:
                raise LMSAuthenticationError("Authentication failed: Still on login page")
            
            logger.info(f"Successfully authenticated user: {username}")
            await page.close()
            
            return self.context
        
        except LMSAuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}", exc_info=True)
            raise LMSAuthenticationError(f"Authentication error: {str(e)}")
    
    async def is_session_valid(self) -> bool:
        """Check if current session is still valid"""
        if not self.context:
            return False
        
        try:
            page = await self.context.new_page()
            await page.goto(settings.lms_base_url, timeout=10000)
            
            # Check if we're redirected to login page
            current_url = page.url
            await page.close()
            
            return settings.lms_login_url not in current_url
        except:
            return False


# Singleton instance
_lms_auth_service = None


def get_lms_auth_service() -> LMSAuthService:
    """Get LMS auth service singleton instance"""
    global _lms_auth_service
    if _lms_auth_service is None:
        _lms_auth_service = LMSAuthService()
    return _lms_auth_service
