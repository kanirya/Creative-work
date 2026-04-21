from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 8002
    log_level: str = "info"

    # Microsoft Azure AD credentials (for OIDC login)
    ms_email: str = ""
    ms_password: str = ""

    # LMS Configuration
    lms_base_url: str = "https://lms.iqra.edu.pk"
    lms_timeout: int = 30000

    # Session persistence
    session_storage_path: str = "/tmp/moodle_session.json"

    # Scraping
    scrape_interval_hours: int = 6

    # API Gateway
    api_gateway_url: str = "http://api-gateway:8080"

    # Database
    database_url: str = ""
    redis_url: str = ""
    cache_ttl_seconds: int = 300

    # OpenAI
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"

    # AI provider
    ai_provider: str = "openai"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
