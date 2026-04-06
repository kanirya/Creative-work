# Iqra University LMS — Microsoft OIDC Login Flow

## Overview

Iqra LMS (`https://lms.iqra.edu.pk`) is a **Moodle** instance that uses the
[Microsoft 365 OIDC plugin](https://github.com/microsoft/moodle-auth_oidc) for authentication.
There is no local username/password login for students — all auth goes through Microsoft Azure AD.

## Azure AD App Registration

| Field | Value |
|---|---|
| Client ID | `fbe1283b-3f94-4a03-a55c-5e4f0c086581` |
| Tenant | `organizations` (multi-tenant, accepts any Microsoft org account) |
| Redirect URI | `https://lms.iqra.edu.pk/auth/oidc/` |
| Scopes | `openid profile email` |
| Resource | `https://graph.microsoft.com` |

## Step-by-Step Login Flow

### Step 1 — Navigate to OIDC entry point
```
GET https://lms.iqra.edu.pk/auth/oidc/?source=loginpage
```
Moodle redirects to Microsoft:
```
https://login.microsoftonline.com/organizations/oauth2/authorize
  ?response_type=code
  &client_id=fbe1283b-3f94-4a03-a55c-5e4f0c086581
  &scope=openid profile email
  &response_mode=form_post
  &redirect_uri=https://lms.iqra.edu.pk/auth/oidc/
  &resource=https://graph.microsoft.com
```

### Step 2 — Microsoft email entry page
- URL contains: `login.microsoftonline.com`
- Selector: `input[type="email"]` or `input[name="loginfmt"]`
- Action: fill email, click `input[type="submit"]` or `button[type="submit"]`
- Wait for: URL to change (next page loads)

### Step 3 — Microsoft password entry page
- URL still contains: `login.microsoftonline.com`
- Selector: `input[type="password"]` or `input[name="passwd"]`
- Action: fill password, click `input[type="submit"]` or `button[type="submit"]`
- Wait for: navigation

### Step 4 — "Stay signed in?" prompt (KMSI)
- URL contains: `login.microsoftonline.com/kmsi`
- Selector for "No": `input[value="No"]` or `button#idBtn_Back`
- Action: click "No" to avoid persistent session issues
- This page may not always appear

### Step 5 — Redirect back to Moodle
- Microsoft POSTs the auth code to `https://lms.iqra.edu.pk/auth/oidc/`
- Moodle processes the code and sets `MoodleSession` cookie
- Final URL: `https://lms.iqra.edu.pk/my/` (dashboard)

### Step 6 — Verify login success
- Check URL contains `lms.iqra.edu.pk` (not `microsoftonline.com`)
- Check for Moodle dashboard elements: `.dashboard-content`, `[data-region="myoverview"]`
- Check for `MoodleSession` cookie in browser context

## Playwright Selectors Reference

```python
# Step 2 - Email
EMAIL_INPUT = 'input[type="email"], input[name="loginfmt"]'
NEXT_BUTTON = 'input[type="submit"][value="Next"], button[type="submit"]'

# Step 3 - Password  
PASSWORD_INPUT = 'input[type="password"], input[name="passwd"]'
SIGNIN_BUTTON = 'input[type="submit"][value="Sign in"], button[type="submit"]'

# Step 4 - Stay signed in
KMSI_NO_BUTTON = 'input[value="No"], button#idBtn_Back, #idBtn_Back'

# Step 6 - Verify dashboard
DASHBOARD_SELECTOR = '[data-region="myoverview"], .dashboard-content, #page-my-index'
```

## Anti-Bot Detection Measures

Microsoft's login page detects automation. Use these Playwright settings:
```python
context = await browser.new_context(
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    viewport={"width": 1920, "height": 1080},
)
await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
```

## Session Cookie

After login, Moodle sets:
- Cookie name: `MoodleSession`
- Domain: `lms.iqra.edu.pk`
- This cookie is used for all subsequent requests

## Known Issues

1. **MFA**: If the Microsoft account has MFA enabled, the flow will pause at the MFA prompt.
   Use a service account without MFA for automated scraping.
2. **Conditional Access**: Microsoft may block logins from unusual locations/IPs.
   Use a consistent IP or whitelist the scraper's IP in Azure AD.
3. **Session Expiry**: Moodle sessions expire after ~2 hours of inactivity.
   Persist cookies and re-authenticate when session expires.
