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
    embedding_model: str = "text-embedding-ada-002"
    max_search_results: int = 5
    similarity_threshold: float = 0.7
    
    # LLM
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.7
    max_tokens: int = 1000

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
