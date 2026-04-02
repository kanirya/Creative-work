from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


class JobType(str, Enum):
    SCRAPING = "scraping"
    TRANSCRIPTION = "transcription"
    BACKUP = "backup"


class JobStatus(str, Enum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScheduleJobRequest(BaseModel):
    student_id: UUID = Field(..., description="Student ID")
    job_type: JobType = Field(..., description="Job type")
    cron_expression: str = Field(..., description="Cron expression for scheduling")


class JobInfo(BaseModel):
    job_id: UUID
    job_type: JobType
    cron_expression: str
    next_run_time: Optional[datetime] = None
    last_run_time: Optional[datetime] = None
    status: JobStatus


class JobExecutionHistory(BaseModel):
    job_id: UUID
    execution_time: datetime
    status: JobStatus
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    active_jobs: int = 0
