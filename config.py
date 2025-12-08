from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Google Gemini
    GOOGLE_API_KEY: str
    GEMINI_MODEL: Optional[str] = "gemini-2.5-flash"
    
    # LLaMAParse
    LLAMAPARSE_API_KEY: str
    
    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    
    # External APIs
    WEATHER_API_KEY: str
    TAVILY_API_KEY: str
    
    # Webhook
    WEBHOOK_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields like Redis settings


settings = Settings()

