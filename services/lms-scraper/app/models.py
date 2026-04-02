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


class ScrapeRequest(BaseModel):
    student_id: UUID = Field(..., description="Student ID")
    lms_username: str = Field(..., min_length=1, description="LMS username")
    lms_password: str = Field(..., min_length=1, description="LMS password")


class CourseData(BaseModel):
    course_code: str
    course_name: str
    instructor: str
    semester: str
    credits: int


class AssignmentData(BaseModel):
    title: str
    description: str
    course_code: str
    due_date: datetime
    max_score: float
    status: str


class AnnouncementData(BaseModel):
    title: str
    content: str
    course_code: str
    posted_date: datetime
    priority: str = "normal"


class ScrapingResult(BaseModel):
    student_id: UUID
    status: ScrapingStatus
    courses_count: int = 0
    assignments_count: int = 0
    announcements_count: int = 0
    error_message: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class ScrapingStatusResponse(BaseModel):
    status: ScrapingStatus
    last_scraped_at: Optional[datetime] = None
    error_message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
