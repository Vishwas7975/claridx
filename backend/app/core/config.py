from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings, loaded from environment variables and backend/.env."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ClariDx API"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str
    test_database_url: str | None = None

    secret_key: str = Field(min_length=32)
    access_token_expire_minutes: int = 30
    jwt_algorithm: Literal["HS256"] = "HS256"

    cors_origins: list[str] = ["http://localhost:5173"]

    model_artifacts_dir: Path = BACKEND_DIR / "ml" / "artifacts"


@lru_cache
def get_settings() -> Settings:
    return Settings()
