# LMS Scraper Troubleshooting Guide

## Common Issues

### 1. Microsoft Blocks Automated Login

**Symptom:** Login fails immediately or redirects to an error page. You may see `LMSAuthenticationError: Login failed`.

**Cause:** Microsoft detects browser automation via the `navigator.webdriver` flag or missing browser fingerprint signals.

**Solutions:**
- The scraper already sets `--disable-blink-features=AutomationControlled` and overrides `navigator.webdriver = undefined`. Verify these are present in `lms_auth.py`.
- Use a realistic user-agent string (Chrome on Windows). The current config uses `Chrome/120.0.0.0`.
- Add a small delay between form interactions (already set to 500ms–2000ms).
- If Microsoft still blocks, try increasing delays in `_full_login()`.
- Use a dedicated service account that has never triggered Microsoft's bot detection.

---

### 2. Session Expiry

**Symptom:** Scraping works initially but fails on subsequent runs with `LMSAuthenticationError: Did not redirect back to Moodle`.

**Cause:** The saved session cookie (`/tmp/moodle_session.json`) has expired. Moodle sessions typically expire after 2–8 hours of inactivity.

**Solutions:**
- Delete the session file to force a fresh login:
  ```bash
  rm /tmp/moodle_session.json
  ```
- The scraper automatically falls back to full re-authentication when the session is invalid. Check logs for `"Saved session has expired"`.
- If running in Docker, ensure the session volume is mounted: `./data/sessions:/tmp`.
- Reduce `scrape_interval_hours` to keep the session active.

---

### 3. MFA / Conditional Access Required

**Symptom:** `MFARequiredError: Microsoft requires MFA. Use a service account without MFA for automated scraping.`

**Cause:** The Microsoft account has Multi-Factor Authentication enabled, which cannot be automated.

**Solutions:**
- Use a dedicated service account with MFA disabled in Azure AD.
- Contact your IT administrator to create a service account with:
  - MFA disabled (or excluded from MFA policy)
  - Conditional Access policy exemption for automated access
- If MFA is mandatory, consider using the MSAL device flow (`msal` library) as a fallback — this requires manual one-time approval.

---

### 4. Moodle Selector Changes

**Symptom:** Scrapers return 0 results or partial data. Logs show `"Could not parse date"` or `"Error extracting course link"`.

**Cause:** The Iqra LMS UI was updated and HTML selectors no longer match.

**Solutions:**
1. Capture fresh HTML fixtures from the real LMS:
   ```bash
   # Run in headed mode to inspect the page
   python -c "
   import asyncio
   from playwright.async_api import async_playwright
   async def capture():
       async with async_playwright() as p:
           browser = await p.chromium.launch(headless=False)
           page = await browser.new_page()
           await page.goto('https://lms.iqra.edu.pk/my/')
           html = await page.content()
           open('tests/fixtures/dashboard_new.html', 'w').write(html)
           await browser.close()
   asyncio.run(capture())
   "
   ```
2. Compare the new HTML with `tests/fixtures/dashboard.html` to identify changed selectors.
3. Update selectors in `services/lms-scraper/app/services/scrapers.py`.
4. Update the fixture files in `tests/fixtures/` with the new HTML.
5. Run unit tests to verify: `pytest tests/test_scrapers_unit.py -v`

---

### 5. Playwright Browser Not Found

**Symptom:** `playwright._impl._api_types.Error: Executable doesn't exist at /root/.cache/ms-playwright/chromium-*/chrome-linux/chrome`

**Cause:** Chromium was not installed in the Docker container.

**Solution:** Verify the Dockerfile contains:
```dockerfile
RUN playwright install-deps chromium && playwright install chromium
```
Rebuild the container: `docker-compose build lms-scraper`

---

### 6. Database Connection Errors

**Symptom:** `psycopg2.OperationalError: could not connect to server`

**Cause:** The API Gateway or PostgreSQL is not reachable from the scraper container.

**Solutions:**
- Ensure all services are running: `docker-compose ps`
- Check `API_GATEWAY_URL` env var points to the correct host (use service name in Docker: `http://api-gateway:8080`)
- Verify PostgreSQL health: `docker-compose exec postgres pg_isready`

---

## Debugging Tips

- Enable debug logging: set `LOG_LEVEL=DEBUG` in the environment.
- Check login failure screenshots saved to `/tmp/login_failure.png`.
- Run integration tests manually (requires real credentials):
  ```bash
  MS_EMAIL=your@email.com MS_PASSWORD=yourpass pytest tests/test_auth_integration.py -v -m integration
  ```
- To test without hitting the real LMS, use the HTML fixtures in `tests/fixtures/` with the unit tests:
  ```bash
  pytest tests/test_scrapers_unit.py tests/test_pipeline_unit.py -v
  ```
