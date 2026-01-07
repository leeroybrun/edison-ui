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
def setup_localhost_auth(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Automatically set up localhost mode for all tests to bypass auth.

    This fixture ensures that tests run in localhost mode where no authentication
    is required. It creates a temporary settings file with exposure_mode set to
    'localhost' and sets the SETTINGS_FILE environment variable.
    """
    settings_file = tmp_path / "test_settings.json"
    settings_file.write_text('{"exposureMode": "localhost", "firstRunComplete": true}')
    monkeypatch.setenv("SETTINGS_FILE", str(settings_file))
