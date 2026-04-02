from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from typing import List, Optional
from uuid import UUID, uuid4
import logging
from datetime import datetime

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.job_metadata = {}  # Store additional job metadata
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shutdown")
    
    def add_job(
        self,
        func,
        trigger,
        job_id: str,
        job_type: str,
        student_id: Optional[UUID] = None,
        **kwargs
    ) -> str:
        """
        Add a job to the scheduler
        
        Args:
            func: Function to execute
            trigger: APScheduler trigger (CronTrigger or IntervalTrigger)
            job_id: Unique job ID
            job_type: Type of job (scraping, transcription, backup)
            student_id: Student ID (optional)
            **kwargs: Additional arguments for APScheduler
        
        Returns:
            Job ID
        """
        try:
            job = self.scheduler.add_job(
                func,
                trigger,
                id=job_id,
                replace_existing=True,
                **kwargs
            )
            
            # Store metadata
            self.job_metadata[job_id] = {
                "job_type": job_type,
                "student_id": str(student_id) if student_id else None,
                "created_at": datetime.utcnow()
            }
            
            logger.info(f"Job added: {job_id} ({job_type})")
            return job_id
        
        except Exception as e:
            logger.error(f"Error adding job: {str(e)}", exc_info=True)
            raise
    
    def remove_job(self, job_id: str) -> bool:
        """
        Remove a job from the scheduler
        
        Args:
            job_id: Job ID to remove
        
        Returns:
            True if successful
        """
        try:
            self.scheduler.remove_job(job_id)
            
            # Remove metadata
            if job_id in self.job_metadata:
                del self.job_metadata[job_id]
            
            logger.info(f"Job removed: {job_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error removing job: {str(e)}", exc_info=True)
            return False
    
    def get_job(self, job_id: str):
        """Get job by ID"""
        return self.scheduler.get_job(job_id)
    
    def get_jobs(self) -> List:
        """Get all jobs"""
        return self.scheduler.get_jobs()
    
    def get_job_metadata(self, job_id: str) -> Optional[dict]:
        """Get job metadata"""
        return self.job_metadata.get(job_id)
    
    def pause_job(self, job_id: str):
        """Pause a job"""
        self.scheduler.pause_job(job_id)
        logger.info(f"Job paused: {job_id}")
    
    def resume_job(self, job_id: str):
        """Resume a job"""
        self.scheduler.resume_job(job_id)
        logger.info(f"Job resumed: {job_id}")


# Singleton instance
_scheduler_service = None


def get_scheduler() -> SchedulerService:
    """Get scheduler service singleton instance"""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service
