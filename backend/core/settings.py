from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    cors_origins: list[str] = ["http://localhost:3000"]

    edison_path: str | None = None
    edison_projects_root: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()

