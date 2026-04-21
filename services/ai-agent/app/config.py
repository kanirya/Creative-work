from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str
    
    # OpenAI
    openai_api_key: str
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8001
    log_level: str = "info"
    
    # Vector Search
    embedding_model: str = "text-embedding-3-small"
    max_search_results: int = 6
    similarity_threshold: float = 0.55
    
    # LLM
    llm_model: str = "gpt-4.1-mini"
    llm_temperature: float = 0.2
    max_tokens: int = 1200

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
