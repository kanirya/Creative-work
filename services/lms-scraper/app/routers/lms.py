"""
LMS API router — exposes all LMS operations to the desktop app.

Endpoints:
  GET  /api/lms/profile
  GET  /api/lms/courses
  GET  /api/lms/assignments/{course_id}
  GET  /api/lms/grades
  GET  /api/lms/grades/{course_id}
  GET  /api/lms/events
  GET  /api/lms/announcements/{course_id}
  GET  /api/lms/attendance/{course_id}
  POST /api/lms/assignments/{assignment_id}/submit
  GET  /api/lms/scrape/all
"""

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.services.lms_auth import LMSAuthenticationError, get_lms_auth_service
from app.services.lms_client import IqraLMSClient

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────


async def get_client() -> IqraLMSClient:
    """Get authenticated LMS client."""
    auth = get_lms_auth_service()
    try:
        ctx = await auth.get_authenticated_context()
        return IqraLMSClient(ctx)
    except LMSAuthenticationError as e:
        raise HTTPException(status_code=401, detail=f"LMS authentication failed: {e}")


def serialize(obj):
    """Make datetime objects JSON-serializable."""
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize(i) for i in obj]
    return obj


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/profile")
async def get_profile():
    """Get logged-in student profile."""
    client = await get_client()
    try:
        return serialize(await client.get_profile())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/courses")
async def get_courses():
    """Get all enrolled courses."""
    client = await get_client()
    try:
        return serialize(await client.get_courses())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assignments/{course_id}")
async def get_assignments(course_id: int):
    """Get all assignments for a course with submission status."""
    client = await get_client()
    try:
        return serialize(await client.get_assignments(course_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/grades")
async def get_grades_overview():
    """Get grade overview for all courses."""
    client = await get_client()
    try:
        return serialize(await client.get_grades_overview())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/grades/{course_id}")
async def get_course_grades(course_id: int):
    """Get detailed grade report for a specific course."""
    client = await get_client()
    try:
        return serialize(await client.get_course_grades(course_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events")
async def get_upcoming_events():
    """Get upcoming calendar events (assignments due, quizzes, attendance)."""
    client = await get_client()
    try:
        return serialize(await client.get_upcoming_events())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/announcements/{course_id}")
async def get_announcements(course_id: int):
    """Get announcements for a course."""
    client = await get_client()
    try:
        return serialize(await client.get_announcements(course_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/attendance/{course_id}")
async def get_attendance(course_id: int):
    """Get attendance record for a course."""
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
    """
    Submit an assignment.
    Accepts a file upload and/or online text.
    """
    if not file and not online_text:
        raise HTTPException(status_code=400, detail="Either file or online_text must be provided")

    client = await get_client()

    # Save uploaded file temporarily
    tmp_path = None
    if file:
        tmp_path = Path(f"/tmp/{file.filename}")
        content = await file.read()
        tmp_path.write_bytes(content)
        logger.info(f"Saved upload to {tmp_path} ({len(content)} bytes)")

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
    """
    Full LMS scrape — returns all courses, assignments, grades,
    events, and announcements in one call.
    """
    client = await get_client()
    try:
        data = await client.scrape_all()
        return serialize(data)
    except Exception as e:
        logger.error(f"Full scrape error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
