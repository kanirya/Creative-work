import whisper
import os
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from app.config import get_settings
from app.models import TranscriptionSegment

logger = logging.getLogger(__name__)
settings = get_settings()


class WhisperService:
    def __init__(self):
        logger.info(f"Loading Whisper model: {settings.whisper_model}")
        self.model = whisper.load_model(
            settings.whisper_model,
            device=settings.whisper_device
        )
        logger.info("Whisper model loaded successfully")
    
    async def transcribe_audio(
        self,
        audio_file_path: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using Whisper
        
        Args:
            audio_file_path: Path to audio file
            language: Language code (optional, auto-detected if None)
        
        Returns:
            Dictionary with transcription results
        """
        try:
            logger.info(f"Starting transcription for: {audio_file_path}")
            
            # Transcribe with Whisper
            result = self.model.transcribe(
                audio_file_path,
                language=language,
                task="transcribe",
                verbose=False
            )
            
            # Extract full text
            text = result.get("text", "").strip()
            
            # Extract segments with timestamps
            segments = []
            for segment in result.get("segments", []):
                segments.append(TranscriptionSegment(
                    text=segment.get("text", "").strip(),
                    start_time=segment.get("start", 0.0),
                    end_time=segment.get("end", 0.0)
                ))
            
            # Detect language
            detected_language = result.get("language", "unknown")
            
            logger.info(f"Transcription completed: {len(text)} characters, {len(segments)} segments, language: {detected_language}")
            
            return {
                "text": text,
                "segments": segments,
                "language": detected_language,
                "duration": segments[-1].end_time if segments else 0.0
            }
        
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}", exc_info=True)
            raise
    
    async def transcribe_with_timestamps(
        self,
        audio_file_path: str,
        language: Optional[str] = None
    ) -> List[TranscriptionSegment]:
        """
        Transcribe audio and return segments with timestamps
        
        Args:
            audio_file_path: Path to audio file
            language: Language code (optional)
        
        Returns:
            List of TranscriptionSegment objects
        """
        result = await self.transcribe_audio(audio_file_path, language)
        return result.get("segments", [])
    
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages
        
        Returns:
            List of language codes
        """
        return list(whisper.tokenizer.LANGUAGES.keys())


# Singleton instance
_whisper_service = None


def get_whisper_service() -> WhisperService:
    """Get Whisper service singleton instance"""
    global _whisper_service
    if _whisper_service is None:
        _whisper_service = WhisperService()
    return _whisper_service
