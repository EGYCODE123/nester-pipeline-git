"""
Application configuration using Pydantic BaseSettings.
Loads settings from environment variables and .env file.
"""
import os
from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))  # Support Railway's PORT env var
    API_LOG_LEVEL: str = "info"
    
    # CORS configuration
    API_ALLOWED_ORIGINS: List[str] = []
    
    # Security
    API_KEY: str  # Required, no default
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 20
    
    # Logging
    LOG_DIR: str = "logs"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()



