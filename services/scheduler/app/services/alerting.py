import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from uuid import UUID
from datetime import datetime

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AlertingService:
    def __init__(self):
        self.alert_email = settings.alert_email
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
    
    async def send_job_failure_alert(
        self,
        job_id: UUID,
        job_type: str,
        error_message: str,
        retry_count: int
    ):
        """
        Send alert email for job failure
        
        Args:
            job_id: Job ID
            job_type: Type of job
            error_message: Error message
            retry_count: Number of retries attempted
        """
        if not self.alert_email or not self.smtp_username:
            logger.warning("Email alerting not configured, skipping alert")
            return
        
        try:
            subject = f"[EduPilot] Job Failure Alert - {job_type}"
            
            body = f"""
Job Failure Alert

Job ID: {job_id}
Job Type: {job_type}
Error: {error_message}
Retry Count: {retry_count}
Time: {datetime.utcnow().isoformat()}

All retry attempts have been exhausted. Manual intervention may be required.

---
EduPilot Scheduler Service
"""
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = self.alert_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Alert sent for job {job_id}")
        
        except Exception as e:
            logger.error(f"Error sending alert: {str(e)}", exc_info=True)


# Singleton instance
_alerting_service = None


def get_alerting_service() -> AlertingService:
    """Get alerting service singleton instance"""
    global _alerting_service
    if _alerting_service is None:
        _alerting_service = AlertingService()
    return _alerting_service
