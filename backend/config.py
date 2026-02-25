"""
GovPreneurs Auto-Proposal System Configuration
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "GovPreneurs Auto-Proposal API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://govpro:govpro_pass@localhost:5432/govpreneurs"
    DATABASE_URL_SYNC: str = "postgresql://govpro:govpro_pass@localhost:5432/govpreneurs"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # SAM.gov API
    SAMGOV_API_KEY: str = ""
    SAMGOV_BASE_URL: str = "https://api.sam.gov/opportunities/v2/search"
    SAMGOV_ATTACHMENT_BASE: str = "https://api.sam.gov/opportunities/v1/resources/files"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    OPENAI_LLM_MODEL: str = "gpt-4o"

    # Gemini (alternative)
    GEMINI_API_KEY: str = ""
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"
    GEMINI_LLM_MODEL: str = "gemini-1.5-pro"

    # Groq
    GROQ_API_KEY: str = ""
    GROQ_LLM_MODEL: str = "llama-3.3-70b-versatile"

    # AI Provider: "openai", "gemini", or "groq"
    AI_PROVIDER: str = "openai"

    # Document Processing
    CHUNK_SIZE_TOKENS: int = 800
    CHUNK_OVERLAP_TOKENS: int = 150
    MAX_CONTEXT_TOKENS: int = 8000

    # Vector Search
    VECTOR_SEARCH_LIMIT: int = 10
    EMBEDDING_DIMENSION: int = 384  # sentence-transformers

    # File Storage
    ATTACHMENT_DIR: str = "./attachments"
    TEMP_DIR: str = "./tmp"

    # Celery Beat Schedule (seconds)
    SAMGOV_POLL_INTERVAL: int = 21600  # 6 hours

    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:3001"]

    # Security
    SECRET_KEY: str = "change-this-in-production-use-strong-secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
