"""
Application Configuration

Uses Pydantic Settings for type-safe configuration management.
All sensitive values should be set via environment variables in production.

Design Decision:
- Using pydantic-settings for automatic env var loading
- Secrets have sensible dev defaults but MUST be overridden in production
"""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "System Design Mentor"
    API_V1_STR: str = "/api/v1"
    
    # Security
    # IMPORTANT: Change these in production via environment variables
    SECRET_KEY: str = "dev-secret-key-change-in-production-minimum-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours for MVP convenience
    
    # Database
    # Format: postgresql://user:password@host:port/dbname
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/design_mentor"
    
    # LLM Configuration (OpenRouter)
    # Get your API key from: https://openrouter.ai/settings/keys
    OPENROUTER_API_KEY: str = ""  # Empty = disabled
    OPENROUTER_MODEL: str = "openai/gpt-3.5-turbo"  # Default model
    
    # LLM Feature Flags
    LLM_ENABLED: bool = True  # Set to False to disable LLM even if API key exists
    LLM_TIMEOUT_SECONDS: int = 30  # Request timeout
    
    # CORS Origins
    # For MVP: localhost ports for development
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # Next.js default
        "http://127.0.0.1:3000",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton settings instance
settings = Settings()
