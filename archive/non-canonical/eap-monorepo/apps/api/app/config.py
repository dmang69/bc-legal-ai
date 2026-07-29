"""Application settings, loaded from environment.

Uses pydantic-settings so validation happens at startup, not at first use.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@db:5432/enterprise_ai",
        description="SQLAlchemy DSN. Must use psycopg driver.",
    )

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Auth
    EAP_COOKIE_SECURE: bool = False
    EAP_ENABLE_REGISTRATION: bool = False
    EAP_BOOTSTRAP_TOKEN: str = ""

    # AI
    AI_PROVIDER: Literal["mock", "openai-compatible"] = "mock"
    OPENAI_COMPAT_BASE_URL: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Uploads
    UPLOAD_DIR: str = "/data/uploads"
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
