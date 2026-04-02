import os
import logging
from pydub import AudioSegment
from typing import Tuple
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AudioValidationError(Exception):
    """Raised when audio validation fails"""
    pass


class AudioValidator:
    def __init__(self):
        self.min_sample_rate = settings.min_audio_sample_rate
    
    def validate_audio_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate audio file quality
        
        Args:
            file_path: Path to audio file
        
        Returns:
            Tuple of (is_valid, error_message)
        
        Raises:
            AudioValidationError: If validation fails
        """
        try:
            # Check file exists
            if not os.path.exists(file_path):
                raise AudioValidationError("Audio file not found")
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise AudioValidationError("Audio file is empty")
            
            if file_size > 100 * 1024 * 1024:  # 100MB limit
                raise AudioValidationError("Audio file too large (max 100MB)")
            
            # Load audio file
            try:
                audio = AudioSegment.from_file(file_path)
            except Exception as e:
                raise AudioValidationError(f"Invalid audio format: {str(e)}")
            
            # Check sample rate
            sample_rate = audio.frame_rate
            if sample_rate < self.min_sample_rate:
                raise AudioValidationError(
                    f"Audio sample rate too low: {sample_rate}Hz (minimum {self.min_sample_rate}Hz)"
                )
            
            # Check duration
            duration_seconds = len(audio) / 1000.0
            if duration_seconds < 1:
                raise AudioValidationError("Audio too short (minimum 1 second)")
            
            if duration_seconds > 3600:  # 1 hour limit
                raise AudioValidationError("Audio too long (maximum 1 hour)")
            
            # Check channels
            channels = audio.channels
            if channels == 0:
                raise AudioValidationError("Audio has no channels")
            
            logger.info(f"Audio validation passed: {sample_rate}Hz, {duration_seconds:.1f}s, {channels} channels")
            
            return True, ""
        
        except AudioValidationError as e:
            logger.warning(f"Audio validation failed: {str(e)}")
            return False, str(e)
        
        except Exception as e:
            logger.error(f"Unexpected error during audio validation: {str(e)}", exc_info=True)
            return False, f"Validation error: {str(e)}"
    
    def get_audio_info(self, file_path: str) -> dict:
        """
        Get audio file information
        
        Args:
            file_path: Path to audio file
        
        Returns:
            Dictionary with audio metadata
        """
        try:
            audio = AudioSegment.from_file(file_path)
            
            return {
                "sample_rate": audio.frame_rate,
                "channels": audio.channels,
                "duration_seconds": len(audio) / 1000.0,
                "frame_width": audio.frame_width,
                "file_size_bytes": os.path.getsize(file_path)
            }
        
        except Exception as e:
            logger.error(f"Error getting audio info: {str(e)}", exc_info=True)
            return {}


# Singleton instance
_audio_validator = None


def get_audio_validator() -> AudioValidator:
    """Get audio validator singleton instance"""
    global _audio_validator
    if _audio_validator is None:
        _audio_validator = AudioValidator()
    return _audio_validator
