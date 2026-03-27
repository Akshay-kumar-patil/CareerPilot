"""
Application configuration using Pydantic Settings.
Loads from .env file and environment variables.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Career Automation & Job Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Auth
    SECRET_KEY: str = "career-platform-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'career_platform.db'}"
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / "data" / "chroma_db")

    # AI Models - Gemini (primary)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # AI Models - OpenAI (fallback)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"

    # AI Models - Ollama (offline fallback)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # Provider routing
    DEFAULT_MODEL_PROVIDER: str = "gemini"  # "gemini", "openai", "ollama", "auto"
    AI_MODE: str = "auto"  # "online", "offline", "auto"

    # Cost Tracking
    ENABLE_COST_TRACKING: bool = True
    MAX_MONTHLY_COST_USD: float = 50.0

    # File Storage
    UPLOAD_DIR: str = str(BASE_DIR / "data" / "uploads")
    GENERATED_DIR: str = str(BASE_DIR / "data" / "generated")
    TEMPLATE_DIR: str = str(BASE_DIR / "templates")

    # GitHub
    GITHUB_TOKEN: Optional[str] = None

    # CORS
    CORS_ORIGINS: list = ["http://localhost:8501", "http://localhost:3000"]

    # Embedding Model
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

# Ensure directories exist
for dir_path in [settings.UPLOAD_DIR, settings.GENERATED_DIR, settings.CHROMA_PERSIST_DIR]:
    os.makedirs(dir_path, exist_ok=True)
