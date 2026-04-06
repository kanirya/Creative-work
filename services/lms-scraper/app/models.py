from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class ScrapingStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# ── Request / Response ────────────────────────────────────────────────────────

class ScrapeRequest(BaseModel):
    student_id: UUID = Field(..., description="EduPilot student ID")
    scrape_types: List[str] = Field(
        default=["courses", "assignments", "grades", "announcements", "schedule", "quizzes"],
        description="Which data types to scrape"
    )


# ── Scraped Data Models ───────────────────────────────────────────────────────

class CourseData(BaseModel):
    course_id: int = Field(..., description="Moodle internal course ID")
    course_code: str
    course_name: str
    instructor: str = ""
    semester: str = ""
    credits: int = 3
    category: str = ""
    url: str = ""


class AssignmentData(BaseModel):
    course_id: int
    course_name: str
    title: str
    description: str = ""
    due_date: Optional[datetime] = None
    max_score: float = 100.0
    submission_status: str = "not_submitted"  # submitted, not_submitted, late
    grading_status: str = "not_graded"        # graded, not_graded
    grade: Optional[float] = None
    url: str = ""


class GradeData(BaseModel):
    course_id: int
    course_name: str
    item_name: str
    grade: Optional[float] = None
    max_grade: Optional[float] = None
    percentage: Optional[float] = None
    feedback: str = ""


class AnnouncementData(BaseModel):
    course_id: int
    course_name: str
    title: str
    content: str = ""
    author: str = ""
    posted_date: Optional[datetime] = None
    url: str = ""
    priority: str = "normal"


class ScheduleEvent(BaseModel):
    event_name: str
    event_type: str = "assignment"  # assignment, quiz, lecture, other
    course_name: str = ""
    course_id: Optional[int] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    description: str = ""
    url: str = ""


class QuizData(BaseModel):
    course_id: int
    course_name: str
    quiz_name: str
    opens_at: Optional[datetime] = None
    closes_at: Optional[datetime] = None
    time_limit: Optional[int] = None  # minutes
    attempts_allowed: Optional[int] = None
    attempt_status: str = "not_attempted"
    best_grade: Optional[float] = None
    url: str = ""


# ── Scraping Result ───────────────────────────────────────────────────────────

class ScrapingResult(BaseModel):
    student_id: UUID
    status: ScrapingStatus
    courses_count: int = 0
    assignments_count: int = 0
    grades_count: int = 0
    announcements_count: int = 0
    events_count: int = 0
    quizzes_count: int = 0
    error_message: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class ScrapingStatusResponse(BaseModel):
    status: ScrapingStatus
    last_scraped_at: Optional[datetime] = None
    error_message: Optional[str] = None
    courses_count: int = 0
    assignments_count: int = 0
    grades_count: int = 0


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
