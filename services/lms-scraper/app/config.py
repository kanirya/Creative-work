from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 8002
    log_level: str = "info"
    
    # LMS Configuration
    lms_base_url: str
    lms_login_url: str
    lms_timeout: int = 30000
    
    # API Gateway
    api_gateway_url: str
    
    # Database
    database_url: str
    
    # OpenAI
    openai_api_key: str
    embedding_model: str = "text-embedding-ada-002"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
