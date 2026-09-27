"""
Application settings — loaded from environment variables / .env file.
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ENV = PROJECT_ROOT / ".env"
BACKEND_ENV = PROJECT_ROOT / "backend" / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(PROJECT_ENV), str(BACKEND_ENV)),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ----- AI -----
    AI_PROVIDER: str = "gemini"
    AI_API_KEY: str = ""
    AI_MODEL: str = "gpt-4o"
    GITHUB_TOKEN: str = ""
    GITHUB_API_URL: str = "https://api.github.com"
    GITHUB_TIMEOUT_SECONDS: int = 30
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"
    GEMINI_FALLBACK_MODEL: str = "gemini-3.5-flash-lite"

    # ----- Backend -----
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # ----- Database -----
    DATABASE_URL: str = "sqlite+aiosqlite:///./a2z_nexus.db"

    # ----- Google Calendar -----
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:4000/api/auth/google/callback"
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    MICROSOFT_TENANT_ID: str = "common"
    MICROSOFT_REDIRECT_URI: str = "http://localhost:4000/api/auth/microsoft/callback"

    # ----- CORS -----
    FRONTEND_URL: str = "http://localhost:5173"

    # ----- Dev -----
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"


settings = Settings()
