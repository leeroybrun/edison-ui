"""Tests for settings endpoints (T011).

RED Phase: These tests MUST fail initially as the endpoints don't exist yet.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.fixture
def clean_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create app with clean settings in tmp location."""
    # Create a fresh settings file location
    settings_file = tmp_path / "settings.json"

    # Set environment variables
    monkeypatch.setenv("SCAN_ROOTS", str(tmp_path / "projects"))
    monkeypatch.setenv("SETTINGS_FILE", str(settings_file))

    # Create projects directory
    (tmp_path / "projects").mkdir()

    # Clear settings cache
    from core.settings import get_settings

    get_settings.cache_clear()

    app = create_app()
    return TestClient(app)


@pytest.fixture
def existing_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create app with existing settings."""
    settings_file = tmp_path / "settings.json"

    # Write existing settings
    settings_data = {
        "scanRoots": [str(tmp_path / "projects")],
        "displayName": "Test User",
        "firstRunComplete": True,
    }
    settings_file.write_text(json.dumps(settings_data))

    # Set environment
    monkeypatch.setenv("SCAN_ROOTS", str(tmp_path / "projects"))
    monkeypatch.setenv("SETTINGS_FILE", str(settings_file))

    (tmp_path / "projects").mkdir()

    from core.settings import get_settings

    get_settings.cache_clear()

    app = create_app()
    return TestClient(app)


class TestGetSettings:
    """Tests for GET /settings endpoint."""

    def test_get_settings_returns_200(self, clean_settings: TestClient) -> None:
        """Should return 200 OK."""
        response = clean_settings.get("/api/v1/settings")
        assert response.status_code == 200

    def test_get_settings_returns_scan_roots(self, clean_settings: TestClient) -> None:
        """Should return scanRoots array."""
        response = clean_settings.get("/api/v1/settings")
        data = response.json()

        assert "scanRoots" in data
        assert isinstance(data["scanRoots"], list)

    def test_get_settings_returns_exposure_mode(
        self, clean_settings: TestClient
    ) -> None:
        """Should return exposureMode (default localhost)."""
        response = clean_settings.get("/api/v1/settings")
        data = response.json()

        assert "exposureMode" in data
        assert data["exposureMode"] == "localhost"

    def test_get_settings_returns_realtime_config(
        self, clean_settings: TestClient
    ) -> None:
        """Should return realtime configuration."""
        response = clean_settings.get("/api/v1/settings")
        data = response.json()

        assert "realtime" in data
        assert "enabled" in data["realtime"]
        assert "watcherEnabled" in data["realtime"]
        assert "pollingIntervalMs" in data["realtime"]

    def test_get_settings_returns_actor(self, clean_settings: TestClient) -> None:
        """Should return actor info (OS user)."""
        response = clean_settings.get("/api/v1/settings")
        data = response.json()

        assert "actor" in data
        assert "osUser" in data["actor"]


class TestUpdateSettings:
    """Tests for PATCH /settings endpoint."""

    def test_update_settings_returns_200(self, clean_settings: TestClient) -> None:
        """Should return 200 on successful update."""
        response = clean_settings.patch(
            "/api/v1/settings", json={"displayName": "New Name"}
        )
        assert response.status_code == 200

    def test_update_settings_returns_updated_fields(
        self, clean_settings: TestClient
    ) -> None:
        """Should return list of updated fields."""
        response = clean_settings.patch(
            "/api/v1/settings", json={"displayName": "New Name"}
        )
        data = response.json()

        assert "updated" in data
        assert "displayName" in data["updated"]

    def test_update_scan_roots(
        self, clean_settings: TestClient, tmp_path: Path
    ) -> None:
        """Should be able to update scanRoots."""
        new_root = str(tmp_path / "new-projects")
        Path(new_root).mkdir()

        response = clean_settings.patch(
            "/api/v1/settings", json={"scanRoots": [new_root]}
        )
        data = response.json()

        assert response.status_code == 200
        assert "scanRoots" in data["updated"]

    def test_update_settings_validates_scan_roots(
        self, clean_settings: TestClient
    ) -> None:
        """Should validate that scan roots exist."""
        response = clean_settings.patch(
            "/api/v1/settings", json={"scanRoots": ["/nonexistent/path"]}
        )
        # Should return 400 for invalid path
        assert response.status_code == 400

    def test_update_settings_ignores_unknown_fields(
        self, clean_settings: TestClient
    ) -> None:
        """Should ignore unknown fields (Pydantic extra='ignore' behavior)."""
        response = clean_settings.patch(
            "/api/v1/settings",
            json={"exposureMode": "network"},  # Not in schema, will be ignored
        )
        # Request succeeds but no fields are updated
        assert response.status_code == 200
        data = response.json()
        # No fields were updated since exposureMode is not in the allowed schema
        assert data["updated"] == []


class TestFirstRunSettings:
    """Tests for first-run settings flow."""

    def test_first_run_check_returns_200(self, clean_settings: TestClient) -> None:
        """Should return 200 OK."""
        response = clean_settings.get("/api/v1/settings/first-run")
        assert response.status_code == 200

    def test_first_run_needs_setup_when_no_settings(
        self, clean_settings: TestClient
    ) -> None:
        """Should indicate needsSetup when no settings configured."""
        response = clean_settings.get("/api/v1/settings/first-run")
        data = response.json()

        assert "needsSetup" in data
        # Fresh install needs setup
        assert data["needsSetup"] is True

    def test_first_run_suggests_roots(self, clean_settings: TestClient) -> None:
        """Should suggest default scan roots."""
        response = clean_settings.get("/api/v1/settings/first-run")
        data = response.json()

        assert "suggestedRoots" in data
        assert isinstance(data["suggestedRoots"], list)

    def test_first_run_no_setup_when_configured(
        self, existing_settings: TestClient
    ) -> None:
        """Should indicate no setup needed when already configured."""
        response = existing_settings.get("/api/v1/settings/first-run")
        data = response.json()

        assert data["needsSetup"] is False

    def test_first_run_complete_returns_200(
        self, clean_settings: TestClient, tmp_path: Path
    ) -> None:
        """Should return 200 on successful first-run completion."""
        projects_dir = tmp_path / "projects"

        response = clean_settings.post(
            "/api/v1/settings/first-run",
            json={"scanRoots": [str(projects_dir)], "displayName": "Test User"},
        )
        assert response.status_code == 200

    def test_first_run_complete_sets_settings(
        self, clean_settings: TestClient, tmp_path: Path
    ) -> None:
        """Should persist settings after first-run completion."""
        projects_dir = tmp_path / "projects"

        clean_settings.post(
            "/api/v1/settings/first-run",
            json={"scanRoots": [str(projects_dir)], "displayName": "Test User"},
        )

        # Verify settings were persisted
        response = clean_settings.get("/api/v1/settings")
        data = response.json()

        assert data["actor"]["displayName"] == "Test User"

    def test_first_run_complete_marks_setup_done(
        self, clean_settings: TestClient, tmp_path: Path
    ) -> None:
        """Should mark first-run as complete."""
        projects_dir = tmp_path / "projects"

        clean_settings.post(
            "/api/v1/settings/first-run",
            json={"scanRoots": [str(projects_dir)], "displayName": "Test User"},
        )

        # Check first-run status
        response = clean_settings.get("/api/v1/settings/first-run")
        data = response.json()

        assert data["needsSetup"] is False

    def test_first_run_validates_scan_roots(self, clean_settings: TestClient) -> None:
        """Should validate that scan roots exist."""
        response = clean_settings.post(
            "/api/v1/settings/first-run",
            json={"scanRoots": ["/nonexistent/path"], "displayName": "Test User"},
        )
        assert response.status_code == 400


class TestSettingsSchemas:
    """Tests for settings-related Pydantic schemas."""

    def test_settings_response_schema(self) -> None:
        """Should validate SettingsResponse schema."""
        from api.schemas.settings import SettingsResponse, RealtimeConfig, ActorInfo

        response = SettingsResponse(
            scan_roots=["~/projects"],
            exposure_mode="localhost",
            realtime=RealtimeConfig(
                enabled=True, watcher_enabled=True, polling_interval_ms=5000
            ),
            actor=ActorInfo(os_user="testuser", display_name=None),
        )

        assert response.scan_roots == ["~/projects"]

    def test_first_run_check_response_schema(self) -> None:
        """Should validate FirstRunCheckResponse schema."""
        from api.schemas.settings import FirstRunCheckResponse

        response = FirstRunCheckResponse(
            needs_setup=True, suggested_roots=["~/projects"]
        )

        assert response.needs_setup is True

    def test_settings_update_request_schema(self) -> None:
        """Should validate SettingsUpdateRequest schema."""
        from api.schemas.settings import SettingsUpdateRequest

        request = SettingsUpdateRequest(
            scan_roots=["~/projects"], display_name="Test User"
        )

        assert request.display_name == "Test User"
