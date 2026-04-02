import psycopg2
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import logging
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.services.scheduler import get_scheduler
from app.services.job_executor import get_job_executor
from app.models import JobType, JobStatus, JobInfo

logger = logging.getLogger(__name__)
settings = get_settings()


class JobManager:
    def __init__(self):
        self.scheduler = get_scheduler()
        self.executor = get_job_executor()
        self.db_connection = None
    
    def _get_db_connection(self):
        """Get database connection"""
        if self.db_connection is None or self.db_connection.closed:
            self.db_connection = psycopg2.connect(settings.database_url)
        return self.db_connection
    
    async def schedule_scraping_job(
        self,
        student_id: UUID,
        lms_username: str,
        lms_password: str,
        cron_expression: str
    ) -> UUID:
        """
        Schedule LMS scraping job for a student
        
        Args:
            student_id: Student ID
            lms_username: LMS username
            lms_password: LMS password
            cron_expression: Cron expression for scheduling
        
        Returns:
            Job ID
        """
        job_id = str(uuid4())
        
        try:
            # Parse cron expression
            trigger = CronTrigger.from_crontab(cron_expression)
            
            # Add job to scheduler
            self.scheduler.add_job(
                func=lambda: self.executor.execute_scraping_job(student_id, lms_username, lms_password),
                trigger=trigger,
                job_id=job_id,
                job_type=JobType.SCRAPING,
                student_id=student_id
            )
            
            # Store job in database
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO scheduled_jobs 
                (id, student_id, job_type, cron_expression, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                job_id,
                str(student_id),
                JobType.SCRAPING,
                cron_expression,
                JobStatus.SCHEDULED,
                datetime.utcnow()
            ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Scraping job scheduled: {job_id} for student {student_id}")
            return UUID(job_id)
        
        except Exception as e:
            logger.error(f"Error scheduling scraping job: {str(e)}", exc_info=True)
            raise
    
    async def schedule_transcription_check_job(self) -> UUID:
        """
        Schedule periodic job to check for new recordings and queue transcriptions
        
        Returns:
            Job ID
        """
        job_id = "transcription_check_job"
        
        try:
            # Create interval trigger (every 5 minutes)
            trigger = IntervalTrigger(minutes=settings.transcription_check_interval_minutes)
            
            # Add job to scheduler
            self.scheduler.add_job(
                func=self._check_and_queue_transcriptions,
                trigger=trigger,
                job_id=job_id,
                job_type=JobType.TRANSCRIPTION
            )
            
            logger.info(f"Transcription check job scheduled: {job_id}")
            return UUID(job_id)
        
        except Exception as e:
            logger.error(f"Error scheduling transcription check job: {str(e)}", exc_info=True)
            raise
    
    async def _check_and_queue_transcriptions(self):
        """Check for new recordings and queue transcriptions"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Find recordings without transcriptions (created in last 24 hours)
            cursor.execute("""
                SELECT lr.id, lr.recording_url
                FROM lecture_recordings lr
                LEFT JOIN transcriptions t ON lr.id = t.recording_id
                WHERE t.id IS NULL
                    AND lr.created_at > NOW() - INTERVAL '24 hours'
                    AND lr.recording_url IS NOT NULL
            """)
            
            recordings = cursor.fetchall()
            cursor.close()
            
            logger.info(f"Found {len(recordings)} recordings to transcribe")
            
            # Queue transcriptions
            for recording_id, recording_url in recordings:
                try:
                    await self.executor.execute_transcription_job(
                        recording_id=UUID(recording_id),
                        audio_file_url=recording_url
                    )
                except Exception as e:
                    logger.error(f"Failed to queue transcription for {recording_id}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error checking for transcriptions: {str(e)}", exc_info=True)
    
    async def schedule_backup_job(self) -> UUID:
        """
        Schedule daily database backup job
        
        Returns:
            Job ID
        """
        job_id = "database_backup_job"
        
        try:
            # Parse backup time (e.g., "02:00")
            hour, minute = map(int, settings.backup_time.split(":"))
            
            # Create cron trigger for daily backup
            trigger = CronTrigger(hour=hour, minute=minute)
            
            # Add job to scheduler
            self.scheduler.add_job(
                func=self.executor.execute_backup_job,
                trigger=trigger,
                job_id=job_id,
                job_type=JobType.BACKUP
            )
            
            logger.info(f"Backup job scheduled: {job_id} at {settings.backup_time} UTC")
            return UUID(job_id)
        
        except Exception as e:
            logger.error(f"Error scheduling backup job: {str(e)}", exc_info=True)
            raise
    
    async def cancel_job(self, job_id: UUID) -> bool:
        """
        Cancel a scheduled job
        
        Args:
            job_id: Job ID
        
        Returns:
            True if successful
        """
        try:
            # Remove from scheduler
            success = self.scheduler.remove_job(str(job_id))
            
            if success:
                # Update database
                conn = self._get_db_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE scheduled_jobs
                    SET status = %s, updated_at = %s
                    WHERE id = %s
                """, (JobStatus.COMPLETED, datetime.utcnow(), str(job_id)))
                
                conn.commit()
                cursor.close()
            
            return success
        
        except Exception as e:
            logger.error(f"Error cancelling job: {str(e)}", exc_info=True)
            return False
    
    async def get_jobs_for_student(self, student_id: UUID) -> List[JobInfo]:
        """
        Get all jobs for a student
        
        Args:
            student_id: Student ID
        
        Returns:
            List of JobInfo objects
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, job_type, cron_expression, status, next_run_time, last_run_time
                FROM scheduled_jobs
                WHERE student_id = %s AND status = %s
                ORDER BY created_at DESC
            """, (str(student_id), JobStatus.SCHEDULED))
            
            jobs = []
            for row in cursor.fetchall():
                job_id, job_type, cron_expr, status, next_run, last_run = row
                
                jobs.append(JobInfo(
                    job_id=UUID(job_id),
                    job_type=job_type,
                    cron_expression=cron_expr,
                    next_run_time=next_run,
                    last_run_time=last_run,
                    status=status
                ))
            
            cursor.close()
            return jobs
        
        except Exception as e:
            logger.error(f"Error getting jobs for student: {str(e)}", exc_info=True)
            return []
    
    async def record_job_execution(
        self,
        job_id: UUID,
        status: JobStatus,
        error_message: Optional[str] = None,
        duration_seconds: Optional[float] = None
    ):
        """
        Record job execution in history
        
        Args:
            job_id: Job ID
            status: Execution status
            error_message: Error message if failed
            duration_seconds: Execution duration
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO job_execution_history 
                (job_id, execution_time, status, error_message, duration_seconds)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                str(job_id),
                datetime.utcnow(),
                status,
                error_message,
                duration_seconds
            ))
            
            # Update last_run_time in scheduled_jobs
            cursor.execute("""
                UPDATE scheduled_jobs
                SET last_run_time = %s, updated_at = %s
                WHERE id = %s
            """, (datetime.utcnow(), datetime.utcnow(), str(job_id)))
            
            conn.commit()
            cursor.close()
        
        except Exception as e:
            logger.error(f"Error recording job execution: {str(e)}", exc_info=True)
    
    async def cleanup_old_history(self):
        """
        Cleanup job execution history older than retention period
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            cutoff_date = datetime.utcnow() - timedelta(days=settings.job_history_retention_days)
            
            cursor.execute("""
                DELETE FROM job_execution_history
                WHERE execution_time < %s
            """, (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            cursor.close()
            
            logger.info(f"Cleaned up {deleted_count} old job execution records")
        
        except Exception as e:
            logger.error(f"Error cleaning up job history: {str(e)}", exc_info=True)
    
    def close(self):
        """Close database connection"""
        if self.db_connection and not self.db_connection.closed:
            self.db_connection.close()


# Singleton instance
_job_manager = None


def get_job_manager() -> JobManager:
    """Get job manager singleton instance"""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager
