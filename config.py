from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Google Gemini
    GOOGLE_API_KEY: str
    
    # LLaMAParse
    LLAMAPARSE_API_KEY: str
    
    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # External APIs
    WEATHER_API_KEY: str
    TAVILY_API_KEY: str
    
    # Webhook
    WEBHOOK_URL: Optional[str] = None
    
    # Chat settings
    MAX_CHAT_HISTORY: int = 20
    TAVILY_CACHE_TTL: int = 600  # 10 minutes
    WEATHER_CACHE_TTL: int = 600  # 10 minutes
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

