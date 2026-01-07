from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))


# Configure pytest-asyncio to auto-detect async tests
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Configure anyio to use asyncio backend."""
    return "asyncio"


@pytest.fixture(autouse=True)
def isolate_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Auto-applied fixture to isolate settings from user's global config.

    This ensures tests use localhost mode by default (no auth required) and
    don't interfere with the user's actual ~/.edison-ui/settings.json.

    The SETTINGS_FILE env var points to a non-existent temp path, causing
    SettingsManager to use defaults (exposure_mode="localhost").

    Returns:
        Path to the settings file (which doesn't exist, triggering defaults).
    """
    settings_path = tmp_path / "test-settings.json"
    monkeypatch.setenv("SETTINGS_FILE", str(settings_path))
    return settings_path
