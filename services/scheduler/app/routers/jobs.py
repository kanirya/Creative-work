from fastapi import APIRouter, Request, HTTPException
from app.models import ScheduleJobRequest, JobInfo, JobStatus, JobType
from app.services.job_manager import get_job_manager
from uuid import UUID
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/schedule", response_model=JobInfo)
async def schedule_job(request: Request, job_request: ScheduleJobRequest):
    """
    Schedule a new job
    """
    logger_adapter = request.state.logger
    logger_adapter.info(f"Scheduling {job_request.job_type} job for student {job_request.student_id}")
    
    try:
        job_manager = get_job_manager()
        
        if job_request.job_type == JobType.SCRAPING:
            # Microsoft credentials are stored in lms-scraper env vars (MS_EMAIL/MS_PASSWORD)
            # No need to pass credentials here — the scraper service reads them from its own env
            job_id = await job_manager.schedule_scraping_job(
                student_id=job_request.student_id,
                cron_expression=job_request.cron_expression,
            )
            
            return JobInfo(
                job_id=job_id,
                job_type=job_request.job_type,
                cron_expression=job_request.cron_expression,
                status=JobStatus.SCHEDULED
            )
        else:
            raise HTTPException(status_code=400, detail=f"Job type {job_request.job_type} not supported yet")
    
    except Exception as e:
        logger_adapter.error(f"Error scheduling job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to schedule job")


@router.delete("/{job_id}")
async def cancel_job(request: Request, job_id: UUID):
    """
    Cancel a scheduled job
    """
    logger_adapter = request.state.logger
    logger_adapter.info(f"Cancelling job {job_id}")
    
    try:
        job_manager = get_job_manager()
        success = await job_manager.cancel_job(job_id)
        
        if success:
            return {"success": True, "message": "Job cancelled"}
        else:
            raise HTTPException(status_code=404, detail="Job not found")
    
    except Exception as e:
        logger_adapter.error(f"Error cancelling job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cancel job")


@router.get("/student/{student_id}")
async def get_student_jobs(request: Request, student_id: UUID):
    """
    Get all jobs for a student
    """
    logger_adapter = request.state.logger
    logger_adapter.info(f"Getting jobs for student {student_id}")
    
    try:
        job_manager = get_job_manager()
        jobs = await job_manager.get_jobs_for_student(student_id)
        
        return jobs
    
    except Exception as e:
        logger_adapter.error(f"Error getting jobs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get jobs")
