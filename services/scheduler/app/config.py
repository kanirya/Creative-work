from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 8004
    log_level: str = "info"
    
    # Database
    database_url: str
    
    # Microservice URLs
    lms_scraper_url: str
    transcription_url: str
    
    # Job Configuration
    scraping_interval_hours: int = 6
    transcription_check_interval_minutes: int = 5
    backup_time: str = "02:00"
    job_history_retention_days: int = 90
    
    # Alerting
    alert_email: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
