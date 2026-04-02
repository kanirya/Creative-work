import httpx
import logging
from uuid import UUID
from datetime import datetime
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError

from app.config import get_settings
from app.services.alerting import get_alerting_service

logger = logging.getLogger(__name__)
settings = get_settings()


class JobExecutor:
    def __init__(self):
        self.lms_scraper_url = settings.lms_scraper_url
        self.transcription_url = settings.transcription_url
        self.alerting_service = get_alerting_service()
    
    async def execute_scraping_job_with_retry(
        self,
        job_id: UUID,
        student_id: UUID,
        lms_username: str,
        lms_password: str
    ):
        """
        Execute scraping job with retry and alerting
        
        Args:
            job_id: Job ID
            student_id: Student ID
            lms_username: LMS username
            lms_password: LMS password
        """
        retry_count = 0
        
        try:
            await self._execute_scraping_with_retry(student_id, lms_username, lms_password)
        except RetryError as e:
            retry_count = 3
            error_message = str(e.last_attempt.exception())
            logger.error(f"Scraping job {job_id} failed after {retry_count} retries")
            
            # Send alert
            await self.alerting_service.send_job_failure_alert(
                job_id=job_id,
                job_type="scraping",
                error_message=error_message,
                retry_count=retry_count
            )
            
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30)
    )
    async def _execute_scraping_with_retry(self, student_id: UUID, lms_username: str, lms_password: str):
        """Execute scraping with retry logic"""
        logger.info(f"Executing scraping job for student {student_id}")
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.lms_scraper_url}/api/scrape",
                json={
                    "student_id": str(student_id),
                    "lms_username": lms_username,
                    "lms_password": lms_password
                }
            )
            
            response.raise_for_status()
            logger.info(f"Scraping job completed for student {student_id}")
    
    async def execute_transcription_job_with_retry(
        self,
        job_id: UUID,
        recording_id: UUID,
        audio_file_url: str
    ):
        """
        Execute transcription job with retry and alerting
        
        Args:
            job_id: Job ID
            recording_id: Recording ID
            audio_file_url: URL to audio file
        """
        retry_count = 0
        
        try:
            await self._execute_transcription_with_retry(recording_id, audio_file_url)
        except RetryError as e:
            retry_count = 3
            error_message = str(e.last_attempt.exception())
            logger.error(f"Transcription job {job_id} failed after {retry_count} retries")
            
            # Send alert
            await self.alerting_service.send_job_failure_alert(
                job_id=job_id,
                job_type="transcription",
                error_message=error_message,
                retry_count=retry_count
            )
            
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30)
    )
    async def _execute_transcription_with_retry(self, recording_id: UUID, audio_file_url: str):
        """Execute transcription with retry logic"""
        logger.info(f"Executing transcription job for recording {recording_id}")
        
        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(
                f"{self.transcription_url}/api/transcribe/queue",
                json={
                    "recording_id": str(recording_id),
                    "audio_file_url": audio_file_url
                }
            )
            
            response.raise_for_status()
            logger.info(f"Transcription job queued for recording {recording_id}")
    
    async def execute_backup_job(self):
        """
        Execute database backup job
        """
        logger.info("Executing database backup job")
        
        try:
            import subprocess
            from datetime import datetime
            
            # Generate backup filename with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_file = f"/backups/edupilot_backup_{timestamp}.sql"
            
            # Execute pg_dump
            result = subprocess.run(
                [
                    "pg_dump",
                    "-h", "localhost",
                    "-U", "postgres",
                    "-d", "edupilot",
                    "-f", backup_file
                ],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Database backup completed: {backup_file}")
            else:
                logger.error(f"Database backup failed: {result.stderr}")
                raise Exception(f"Backup failed: {result.stderr}")
        
        except Exception as e:
            logger.error(f"Backup job failed: {str(e)}", exc_info=True)
            raise


# Singleton instance
_job_executor = None


def get_job_executor() -> JobExecutor:
    """Get job executor singleton instance"""
    global _job_executor
    if _job_executor is None:
        _job_executor = JobExecutor()
    return _job_executor
