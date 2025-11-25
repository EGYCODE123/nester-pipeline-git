"""
Application configuration using Pydantic BaseSettings.
Loads settings from environment variables and .env file.
"""
import os
import json
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))  # Support Railway's PORT env var
    API_LOG_LEVEL: str = "info"
    
    # CORS configuration - accepts comma-separated string or JSON array
    API_ALLOWED_ORIGINS: Union[List[str], str] = []
    
    @field_validator('API_ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_origins(cls, v):
        """Parse API_ALLOWED_ORIGINS from string to list."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Handle empty string
            if not v or v.strip() == '':
                return []
            # Try to parse as JSON first
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass
            # If not JSON, treat as comma-separated string
            # Split by comma and strip whitespace
            origins = [origin.strip() for origin in v.split(',') if origin.strip()]
            return origins
        return []
    
    # Security
    API_KEY: str = ""  # Optional for now - set in Railway Variables
    
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



