from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from app.models import (
    TranscriptionQueueRequest,
    TranscriptionResult,
    TranscriptionStatusResponse,
    TranscriptionTextResponse,
    TranscriptionStatus
)
from app.services.audio_validator import get_audio_validator, AudioValidationError
from app.services.whisper_service import get_whisper_service
from app.services.transcription_storage import get_transcription_storage_service
from uuid import UUID
from datetime import datetime
import logging
import httpx
import os

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for transcription status
transcription_status_store = {}


async def perform_transcription(recording_id: UUID, audio_file_url: str):
    """Background task to perform transcription"""
    logger.info(f"Starting background transcription for recording {recording_id}")
    
    # Update status to processing
    transcription_status_store[str(recording_id)] = {
        "status": TranscriptionStatus.PROCESSING,
        "completed_at": None,
        "error_message": None
    }
    
    audio_validator = get_audio_validator()
    whisper_service = get_whisper_service()
    storage_service = get_transcription_storage_service()
    
    audio_file_path = None
    
    try:
        # Download audio file
        logger.info(f"Downloading audio from: {audio_file_url}")
        async with httpx.AsyncClient() as client:
            response = await client.get(audio_file_url, timeout=60.0)
            response.raise_for_status()
            
            # Save to temporary file
            audio_file_path = f"/tmp/audio/{recording_id}.mp3"
            os.makedirs(os.path.dirname(audio_file_path), exist_ok=True)
            
            with open(audio_file_path, "wb") as f:
                f.write(response.content)
        
        logger.info(f"Audio downloaded: {audio_file_path}")
        
        # Validate audio quality
        is_valid, error_message = audio_validator.validate_audio_file(audio_file_path)
        if not is_valid:
            raise AudioValidationError(error_message)
        
        # Transcribe audio
        result = await whisper_service.transcribe_audio(audio_file_path)
        
        # Store transcription and generate embeddings
        success = await storage_service.store_transcription(
            recording_id=recording_id,
            text=result["text"],
            segments=result["segments"],
            language=result["language"],
            duration=result["duration"]
        )
        
        if not success:
            raise Exception("Failed to store transcription")
        
        # Update status to completed
        transcription_status_store[str(recording_id)] = {
            "status": TranscriptionStatus.COMPLETED,
            "completed_at": datetime.utcnow(),
            "error_message": None
        }
        
        logger.info(f"Transcription completed for recording {recording_id}")
    
    except AudioValidationError as e:
        logger.error(f"Audio validation failed for recording {recording_id}: {str(e)}")
        transcription_status_store[str(recording_id)] = {
            "status": TranscriptionStatus.FAILED,
            "completed_at": None,
            "error_message": f"Audio validation failed: {str(e)}"
        }
    
    except Exception as e:
        logger.error(f"Transcription failed for recording {recording_id}: {str(e)}", exc_info=True)
        transcription_status_store[str(recording_id)] = {
            "status": TranscriptionStatus.FAILED,
            "completed_at": None,
            "error_message": str(e)
        }
    
    finally:
        # Cleanup temporary file
        if audio_file_path and os.path.exists(audio_file_path):
            try:
                os.remove(audio_file_path)
                logger.info(f"Cleaned up temporary file: {audio_file_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary file: {str(e)}")


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
        
        # Add transcription task to background
        background_tasks.add_task(
            perform_transcription,
            queue_request.recording_id,
            queue_request.audio_file_url
        )
        
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
    
    storage_service = get_transcription_storage_service()
    transcription = await storage_service.get_transcription(recording_id)
    
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    return TranscriptionTextResponse(
        text=transcription["text"],
        segments=transcription["segments"]
    )
