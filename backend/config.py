"""
Application configuration using Pydantic Settings.
Loads from .env file and environment variables.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional, List

BASE_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_SECRET = "career-platform-secret-key-change-in-production"


class Settings(BaseSettings):
    APP_NAME: str = "Career Automation & Job Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    SECRET_KEY: str = _DEFAULT_SECRET
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'career_platform.db'}"
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / "data" / "chroma_db")

    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017/"
    MONGODB_DB_NAME: str = "users"

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"
    FRONTEND_URL: str = "http://localhost:8501"

    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"  # Updated to latest Gemini model

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"

    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    DEFAULT_MODEL_PROVIDER: str = "gemini"
    AI_MODE: str = "auto"

    ENABLE_COST_TRACKING: bool = True
    MAX_MONTHLY_COST_USD: float = 50.0

    UPLOAD_DIR: str = str(BASE_DIR / "data" / "uploads")
    GENERATED_DIR: str = str(BASE_DIR / "data" / "generated")
    TEMPLATE_DIR: str = str(BASE_DIR / "templates")
    TEMPLATE_NAME: str = "resume_reference.html"  # Default template name

    GITHUB_TOKEN: Optional[str] = None

    # Rate limiting settings
    RESUME_GENERATION_LIMIT_PER_HOUR: int = 10
    COVER_LETTER_LIMIT_PER_HOUR: int = 20
    INTERVIEW_LIMIT_PER_HOUR: int = 15

    # File cleanup settings
    FILE_RETENTION_DAYS: int = 7  # Keep generated files for 7 days
    RESUME_RETENTION_DAYS: int = 90  # Keep inactive resumes for 90 days before soft delete
    CLEANUP_BATCH_SIZE: int = 100  # Delete 100 files at a time
    ENABLE_AUTO_CLEANUP: bool = True  # Enable automatic cleanup scheduler

    # File size limits (in bytes)
    MAX_PDF_SIZE_BYTES: int = 5 * 1024 * 1024  # 5MB
    MAX_DOCX_SIZE_BYTES: int = 10 * 1024 * 1024  # 10MB
    MAX_TXT_SIZE_BYTES: int = 2 * 1024 * 1024  # 2MB
    MAX_UPLOAD_SIZE_BYTES: int = 20 * 1024 * 1024  # 20MB

    # FIX: typed as List[str] so CORS_ORIGINS works correctly with middleware
    CORS_ORIGINS: List[str] = [
        "http://localhost:8501",
        "http://localhost:8502",
        "http://localhost:3000",
        "https://career-portal-m5re.onrender.com",
    ]

    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

# FIX: Raise loud error if default secret key used in production
if not settings.DEBUG and settings.SECRET_KEY == _DEFAULT_SECRET:
    raise RuntimeError(
        "SECURITY ERROR: SECRET_KEY is still the default value. "
        "Set a strong random SECRET_KEY in your .env before running in production."
    )

# Ensure required directories exist
for dir_path in [settings.UPLOAD_DIR, settings.GENERATED_DIR, settings.CHROMA_PERSIST_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# Log configuration on startup (only in debug mode)
if settings.DEBUG:
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Application: {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Default AI Provider: {settings.DEFAULT_MODEL_PROVIDER}")
    logger.info(f"Database: {settings.DATABASE_URL}")
    logger.info(f"File Retention: {settings.FILE_RETENTION_DAYS} days")
    logger.info(f"Auto Cleanup: {'Enabled' if settings.ENABLE_AUTO_CLEANUP else 'Disabled'}")
