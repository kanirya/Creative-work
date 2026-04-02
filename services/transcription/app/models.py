from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class TranscriptionStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TranscriptionQueueRequest(BaseModel):
    recording_id: UUID = Field(..., description="Recording ID")
    audio_file_url: str = Field(..., description="URL to audio file")


class TranscriptionSegment(BaseModel):
    text: str
    start_time: float
    end_time: float


class TranscriptionResult(BaseModel):
    recording_id: UUID
    status: TranscriptionStatus
    text: Optional[str] = None
    segments: List[TranscriptionSegment] = Field(default_factory=list)
    language: Optional[str] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None


class TranscriptionStatusResponse(BaseModel):
    status: TranscriptionStatus
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class TranscriptionTextResponse(BaseModel):
    text: str
    segments: List[TranscriptionSegment]


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    whisper_model: str
