from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 8003
    log_level: str = "info"
    
    # Whisper Configuration
    whisper_model: str = "base"
    whisper_device: str = "cpu"
    min_audio_sample_rate: int = 16000
    
    # Database
    database_url: str
    
    # OpenAI
    openai_api_key: str
    embedding_model: str = "text-embedding-ada-002"
    
    # Storage
    audio_storage_path: str = "/tmp/audio"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
