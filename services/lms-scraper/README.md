# EduPilot LMS Scraper Service

Scrapes real student data from **Iqra University LMS** (`https://lms.iqra.edu.pk`) using
Playwright browser automation with **Microsoft Azure AD OIDC** authentication.

## Authentication

Iqra LMS uses Microsoft 365 OIDC — there is no local username/password login.
The scraper automates the full Microsoft login flow:

1. Navigate to `https://lms.iqra.edu.pk/auth/oidc/?source=loginpage`
2. Enter Microsoft email → Next
3. Enter Microsoft password → Sign in
4. Handle "Stay signed in?" → No
5. Verify Moodle dashboard is reached
6. Save session cookies to disk for reuse

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `MS_EMAIL` | Microsoft 365 email (Iqra student email) | `student@iqra.edu.pk` |
| `MS_PASSWORD` | Microsoft 365 password | `YourPassword` |
| `SESSION_STORAGE_PATH` | Path to persist session cookies | `/tmp/moodle_session.json` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |
| `OPENAI_API_KEY` | OpenAI API key for embeddings | `sk-...` |
| `API_GATEWAY_URL` | EduPilot API Gateway URL | `http://api-gateway:8080` |

## Data Scraped

| Data Type | Source |
|---|---|
| Courses | Dashboard → My Courses |
| Assignments | Per-course assignment index |
| Grades | Grade overview + per-course grade report |
| Announcements | Course announcement forums |
| Schedule | Moodle calendar (upcoming events) |
| Quizzes | Per-course quiz activities |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/scrape/` | Trigger scraping for a student |
| `GET` | `/api/scrape/status/{student_id}` | Get scraping status |
| `GET` | `/health` | Health check |

### Trigger Scraping

```json
POST /api/scrape/
{
  "student_id": "uuid-here",
  "scrape_types": ["courses", "assignments", "grades", "announcements", "schedule", "quizzes"]
}
```

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Set credentials
export MS_EMAIL=muhammad.141510.isb@iqra.edu.pk
export MS_PASSWORD=YourPassword
export DATABASE_URL=postgresql://edupilot:password@localhost:5432/edupilot
export OPENAI_API_KEY=sk-...

# Run service
uvicorn app.main:app --reload --port 8002
```

## Running Tests

```bash
# Unit tests (no credentials needed)
pytest tests/test_scrapers_unit.py -v

# Integration tests (requires real credentials)
MS_EMAIL=... MS_PASSWORD=... pytest -m integration -v
```

## Troubleshooting

**Microsoft blocks automated login**
- Ensure `--disable-blink-features=AutomationControlled` is set (already configured)
- Use a consistent IP address — Microsoft may block logins from new locations

**Session expired**
- Delete `SESSION_STORAGE_PATH` file to force re-authentication
- Sessions typically last 2-8 hours

**MFA required**
- Use a service account without MFA enabled
- Contact Iqra IT to create a dedicated scraper account

**Moodle selectors changed after LMS update**
- Update selectors in `app/services/scrapers.py`
- Refer to `docs/moodle-structure.md` for selector reference
- Save new HTML fixtures to `tests/fixtures/`
