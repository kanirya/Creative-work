"""
LMS API router — all LMS operations including real-time login.

POST /api/lms/login              — start Microsoft OIDC login
GET  /api/lms/login/status       — poll login status (returns MFA number)
POST /api/lms/login/clear        — clear session / logout
GET  /api/lms/profile
GET  /api/lms/courses
GET  /api/lms/assignments/{course_id}
GET  /api/lms/assignments/all    — all assignments across all courses
GET  /api/lms/grades
GET  /api/lms/grades/{course_id}
GET  /api/lms/events
GET  /api/lms/announcements/{course_id}
POST /api/lms/assignments/{assignment_id}/submit
GET  /api/lms/scrape/all
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.lms_auth import LMSAuthenticationError, get_lms_auth_service
from app.services.lms_client import IqraLMSClient

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Login state (in-memory) ───────────────────────────────────────────────────

_login_state: dict = {
    "status": "idle",   # idle | logging_in | mfa_pending | logged_in | failed
    "mfa_number": None,
    "error": None,
    "profile": None,
}


class LoginRequest(BaseModel):
    email: str
    password: str


# ── Helpers ───────────────────────────────────────────────────────────────────


async def get_client() -> IqraLMSClient:
    auth = get_lms_auth_service()
    try:
        ctx = await auth.get_authenticated_context()
        return IqraLMSClient(ctx)
    except LMSAuthenticationError as e:
        raise HTTPException(status_code=401, detail=f"LMS authentication failed: {e}")


def serialize(obj):
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize(i) for i in obj]
    return obj


# ── Login endpoints ───────────────────────────────────────────────────────────


async def _do_login(email: str, password: str):
    """Background task: full Microsoft OIDC login flow."""
    global _login_state
    import app.services.lms_auth as auth_module

    # Set credentials
    os.environ["MS_EMAIL"] = email
    os.environ["MS_PASSWORD"] = password

    # Reset singleton to pick up new credentials
    if auth_module._instance:
        try:
            await auth_module._instance.close()
        except Exception:
            pass
    auth_module._instance = None

    _login_state.update(status="logging_in", mfa_number=None, error=None, profile=None)

    try:
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

            # Step 1: OIDC entry
            await page.goto(
                "https://lms.iqra.edu.pk/auth/oidc/?source=loginpage",
                wait_until="domcontentloaded", timeout=30_000,
            )
            await asyncio.sleep(2)

            # Step 2: Email
            await page.wait_for_selector('input[name="loginfmt"]', timeout=15_000)
            await page.fill('input[name="loginfmt"]', email)
            await asyncio.sleep(0.6)
            await page.keyboard.press("Enter")
            await asyncio.sleep(4)

            # Step 3: Password
            await page.wait_for_selector('input[name="passwd"]', timeout=15_000)
            await page.fill('input[name="passwd"]', password)
            await asyncio.sleep(0.6)
            await page.keyboard.press("Enter")
            await asyncio.sleep(6)

            # Step 4: Check for MFA
            mfa_number = None
            for sel in ['[data-testid="displaySign"]', '#idRichContext_DisplaySign', '.display-sign']:
                el = await page.query_selector(sel)
                if el:
                    text = (await el.inner_text()).strip()
                    if text and text.isdigit():
                        mfa_number = text
                        break

            if mfa_number:
                _login_state.update(status="mfa_pending", mfa_number=mfa_number)
                logger.info(f"MFA required: {mfa_number}")

                # Wait for approval
                approved = False
                for _ in range(90):
                    await asyncio.sleep(1)
                    try:
                        url = page.url
                        if "lms.iqra.edu.pk" in url or "kmsi" in url:
                            approved = True
                            break
                        still = await page.query_selector('[data-testid="displaySign"], #idRichContext_DisplaySign')
                        if not still:
                            approved = True
                            break
                    except Exception:
                        pass

                if not approved:
                    _login_state.update(status="failed", error="MFA approval timed out")
                    await browser.close()
                    return

                await asyncio.sleep(3)

            # Step 5: KMSI
            try:
                kmsi = await page.query_selector('#idBtn_Back')
                if kmsi:
                    await kmsi.click()
                    await asyncio.sleep(3)
            except Exception:
                pass

            # Step 6: Verify
            if "lms.iqra.edu.pk" in page.url and "microsoftonline" not in page.url:
                state = await ctx.storage_state()
                session_path = Path(os.environ.get("SESSION_STORAGE_PATH", "lms_session_test.json"))
                session_path.write_text(json.dumps(state))

                # Get profile
                client = IqraLMSClient(ctx)
                try:
                    profile = await client.get_profile()
                    _login_state.update(status="logged_in", mfa_number=None, profile=profile)
                except Exception:
                    _login_state.update(status="logged_in", mfa_number=None)

                logger.info("Login successful")
            else:
                _login_state.update(status="failed", error=f"Login failed. URL: {page.url}")

            await browser.close()

    except Exception as e:
        _login_state.update(status="failed", error=str(e))
        logger.error(f"Login error: {e}", exc_info=True)


@router.post("/login")
async def login(request: LoginRequest, background_tasks: BackgroundTasks):
    """Start Microsoft OIDC login. Poll /login/status for MFA number and completion."""
    global _login_state
    _login_state = {"status": "logging_in", "mfa_number": None, "error": None, "profile": None}
    background_tasks.add_task(_do_login, request.email, request.password)
    return {"status": "logging_in", "message": "Login started. Poll /login/status for updates."}


@router.get("/login/status")
async def login_status():
    """Poll login status. When status='mfa_pending', show mfa_number to user."""
    return _login_state


@router.post("/login/clear")
async def clear_session():
    """Clear saved session to force re-login."""
    import app.services.lms_auth as auth_module
    session_path = Path(os.environ.get("SESSION_STORAGE_PATH", "lms_session_test.json"))
    if session_path.exists():
        session_path.unlink()
    if auth_module._instance:
        try:
            await auth_module._instance.close()
        except Exception:
            pass
    auth_module._instance = None
    global _login_state
    _login_state = {"status": "idle", "mfa_number": None, "error": None, "profile": None}
    return {"message": "Session cleared"}


# ── Data endpoints ────────────────────────────────────────────────────────────


@router.get("/profile")
async def get_profile():
    client = await get_client()
    try:
        return serialize(await client.get_profile())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/courses")
async def get_courses():
    client = await get_client()
    try:
        return serialize(await client.get_courses())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assignments/all")
async def get_all_assignments():
    """Get all assignments across all enrolled courses."""
    client = await get_client()
    try:
        courses = await client.get_courses()
        all_assignments = []
        for course in courses:
            try:
                assigns = await client.get_assignments(course["id"])
                all_assignments.extend(assigns)
            except Exception as e:
                logger.warning(f"Could not get assignments for course {course['id']}: {e}")
        return serialize(all_assignments)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assignments/{course_id}")
async def get_assignments(course_id: int):
    """Get all assignments for a specific course."""
    client = await get_client()
    try:
        return serialize(await client.get_assignments(course_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/grades")
async def get_grades_overview():
    client = await get_client()
    try:
        return serialize(await client.get_grades_overview())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/grades/{course_id}")
async def get_course_grades(course_id: int):
    client = await get_client()
    try:
        return serialize(await client.get_course_grades(course_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events")
async def get_upcoming_events():
    client = await get_client()
    try:
        return serialize(await client.get_upcoming_events())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/announcements/{course_id}")
async def get_announcements(course_id: int):
    client = await get_client()
    try:
        return serialize(await client.get_announcements(course_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/attendance/{course_id}")
async def get_attendance(course_id: int):
    client = await get_client()
    try:
        return serialize(await client.get_attendance(course_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assignments/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: int,
    file: Optional[UploadFile] = File(None),
    online_text: Optional[str] = Form(None),
):
    if not file and not online_text:
        raise HTTPException(status_code=400, detail="Either file or online_text must be provided")

    client = await get_client()
    tmp_path = None
    if file:
        import tempfile
        suffix = Path(file.filename).suffix if file.filename else ".bin"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        content = await file.read()
        tmp.write(content)
        tmp.close()
        tmp_path = Path(tmp.name)

    try:
        result = await client.submit_assignment_file(
            assignment_id=assignment_id,
            file_path=str(tmp_path) if tmp_path else "",
            online_text=online_text or "",
        )
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()


@router.get("/scrape/all")
async def scrape_all():
    client = await get_client()
    try:
        data = await client.scrape_all()
        return serialize(data)
    except Exception as e:
        logger.error(f"Full scrape error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
