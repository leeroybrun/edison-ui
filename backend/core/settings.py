from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_comma_list(v: str) -> list[str]:
    """Parse comma-separated string into a list."""
    if not v:
        return []
    return [item.strip() for item in v.split(",") if item.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    cors_origins: list[str] = ["http://localhost:3000"]

    edison_path: str | None = None
    edison_projects_root: str | None = None

    # Project discovery configuration (T006)
    # Store as strings to support comma-separated env vars, expose as list via property
    scan_roots_raw: str = Field(
        default="~/projects",
        validation_alias="SCAN_ROOTS",
    )
    scan_ignore_patterns_raw: str = Field(
        default="node_modules,.git,.venv,__pycache__",
        validation_alias="SCAN_IGNORE_PATTERNS",
    )
    pin_storage_path: str = "~/.edison-ui/pins.json"

    @property
    def scan_roots(self) -> list[str]:
        """Return scan_roots as a list."""
        return _parse_comma_list(self.scan_roots_raw)

    @property
    def scan_ignore_patterns(self) -> list[str]:
        """Return scan_ignore_patterns as a list."""
        return _parse_comma_list(self.scan_ignore_patterns_raw)

    def get_expanded_scan_roots(self) -> list[str]:
        """Return scan_roots with tilde expanded to absolute paths."""
        return [str(Path(root).expanduser().resolve()) for root in self.scan_roots]

    def get_expanded_pin_storage_path(self) -> str | None:
        """Return pin_storage_path with tilde expanded."""
        if not self.pin_storage_path:
            return None
        return str(Path(self.pin_storage_path).expanduser().resolve())


@lru_cache
def get_settings() -> Settings:
    return Settings()

