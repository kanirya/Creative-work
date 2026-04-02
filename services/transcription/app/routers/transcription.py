from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from app.models import (
    TranscriptionQueueRequest,
    TranscriptionResult,
    TranscriptionStatusResponse,
    TranscriptionTextResponse,
    TranscriptionStatus
)
from uuid import UUID
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for transcription status
transcription_status_store = {}


@router.post("/queue", response_model=TranscriptionResult)
async def queue_transcription(
    request: Request,
    queue_request: TranscriptionQueueRequest,
    background_tasks: BackgroundTasks
):
    """
    Queue a recording for transcription
    """
    logger_adapter = request.state.logger
    logger_adapter.info(f"Queuing transcription for recording {queue_request.recording_id}")
    
    try:
        # Store initial status
        transcription_status_store[str(queue_request.recording_id)] = {
            "status": TranscriptionStatus.QUEUED,
            "completed_at": None,
            "error_message": None
        }
        
        # TODO: Add background task for transcription
        # This will be implemented in tasks 10.2, 10.4, 10.5
        
        return TranscriptionResult(
            recording_id=queue_request.recording_id,
            status=TranscriptionStatus.QUEUED
        )
    
    except Exception as e:
        logger_adapter.error(f"Error queuing transcription: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to queue transcription")


@router.get("/status/{recording_id}", response_model=TranscriptionStatusResponse)
async def get_transcription_status(request: Request, recording_id: UUID):
    """
    Get transcription status for a recording
    """
    logger_adapter = request.state.logger
    logger_adapter.info(f"Getting transcription status for recording {recording_id}")
    
    status_data = transcription_status_store.get(str(recording_id))
    
    if not status_data:
        return TranscriptionStatusResponse(
            status=TranscriptionStatus.QUEUED,
            completed_at=None,
            error_message=None
        )
    
    return TranscriptionStatusResponse(**status_data)


@router.get("/{recording_id}", response_model=TranscriptionTextResponse)
async def get_transcription(request: Request, recording_id: UUID):
    """
    Get transcription text and segments for a recording
    """
    logger_adapter = request.state.logger
    logger_adapter.info(f"Getting transcription for recording {recording_id}")
    
    # TODO: Retrieve from database
    # This will be implemented in task 10.5
    
    raise HTTPException(status_code=404, detail="Transcription not found")
