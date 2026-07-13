"""
Application Configuration — loaded from environment variables via Pydantic Settings.
"""
from __future__ import annotations
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────────
    APP_NAME: str = "AI Talent Scout Pro X"
    APP_VERSION: str = "3.0.0"  # Stepping up to enterprise version
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"

    # ── Security ─────────────────────────────────────────────────────────
    SECRET_KEY: str = "SUPER-SECRET-KEY-CHANGE-IN-PROD"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    RATE_LIMIT_REQUESTS: int = 100

    # ── PostgreSQL ───────────────────────────────────────────────────────
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "talent_scout"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/talent_scout"
    SYNC_DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/talent_scout"

    # ── Redis ────────────────────────────────────────────────────────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Celery ───────────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── CORS ─────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ── File Upload ──────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 20  # Increased for enterprise resumes
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt"]
    UPLOAD_DIR: str = "uploads"

    # ── ML ───────────────────────────────────────────────────────────────
    ML_MODELS_DIR: str = "ml_models"
    SENTENCE_MODEL_NAME: str = "all-MiniLM-L6-v2"
    SPACY_MODEL: str = "en_core_web_md"
    FAISS_INDEX_PATH: str = "ml_models/candidate_vectors.faiss"

    # ── Logging ──────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
