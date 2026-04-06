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
        scrape_types: Optional[list] = None,
    ):
        """
        Execute scraping job with retry and alerting.
        Microsoft credentials are read from environment variables (MS_EMAIL, MS_PASSWORD)
        configured in the lms-scraper service — not passed here.

        Args:
            job_id: Job ID
            student_id: Student ID
            scrape_types: List of data types to scrape (default: all)
        """
        if scrape_types is None:
            scrape_types = ["courses", "assignments", "grades", "announcements", "schedule", "quizzes"]

        consecutive_failures = getattr(self, f"_failures_{student_id}", 0)

        try:
            await self._execute_scraping_with_retry(student_id, scrape_types)
            # Reset failure counter on success
            setattr(self, f"_failures_{student_id}", 0)

            # Health check: verify data was actually stored
            await self._verify_scraping_result(student_id)

        except RetryError as e:
            consecutive_failures += 1
            setattr(self, f"_failures_{student_id}", consecutive_failures)
            error_message = str(e.last_attempt.exception())
            logger.error(f"Scraping job {job_id} failed after 3 retries (total failures: {consecutive_failures})")

            await self.alerting_service.send_job_failure_alert(
                job_id=job_id,
                job_type="scraping",
                error_message=error_message,
                retry_count=3,
            )
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
    )
    async def _execute_scraping_with_retry(self, student_id: UUID, scrape_types: list):
        """Trigger scraping via lms-scraper service API."""
        logger.info(f"Triggering scraping for student {student_id}, types={scrape_types}")

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.lms_scraper_url}/api/scrape/",
                json={
                    "student_id": str(student_id),
                    "scrape_types": scrape_types,
                },
            )
            response.raise_for_status()
            logger.info(f"Scraping triggered for student {student_id}: {response.json()}")

    async def _verify_scraping_result(self, student_id: UUID):
        """
        Poll scraping status until completed or failed.
        If 0 courses returned, log a warning (possible auth failure).
        """
        import asyncio

        max_wait_seconds = 600  # 10 minutes max
        poll_interval = 15
        elapsed = 0

        async with httpx.AsyncClient(timeout=30.0) as client:
            while elapsed < max_wait_seconds:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

                try:
                    resp = await client.get(
                        f"{self.lms_scraper_url}/api/scrape/status/{student_id}"
                    )
                    data = resp.json()
                    status = data.get("status")

                    if status == "completed":
                        courses = data.get("courses_count", 0)
                        if courses == 0:
                            logger.warning(
                                f"Scraping completed for student {student_id} but 0 courses found. "
                                "Possible auth failure or LMS structure change."
                            )
                        else:
                            logger.info(
                                f"Scraping verified for student {student_id}: "
                                f"{courses} courses, {data.get('assignments_count', 0)} assignments"
                            )
                        return

                    elif status == "failed":
                        error = data.get("error_message", "unknown error")
                        raise Exception(f"Scraping failed: {error}")

                except httpx.HTTPError as e:
                    logger.debug(f"Status poll error: {e}")
                    continue

        logger.warning(f"Scraping status check timed out for student {student_id}")
    
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
