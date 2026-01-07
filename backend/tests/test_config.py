"""Tests for pack/config endpoints (T076).

RED Phase: These tests MUST fail initially as the endpoints don't exist yet.

Implements tests for:
- GET /projects/{projectId}/config - Get project configuration
- GET /projects/{projectId}/packs - List available packs
- GET /projects/{projectId}/packs/{packId} - Get pack details
- POST /projects/{projectId}/config/preview - Preview config edit
- POST /projects/{projectId}/config - Apply config edit
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.fixture
def mock_edison_project_with_config(tmp_path: Path) -> Path:
    """Create a mock Edison project with configuration."""
    project_path = tmp_path / "test-project"
    project_path.mkdir()

    # Create .edison directory with config
    edison_dir = project_path / ".edison"
    edison_dir.mkdir()

    # Create config directory with project config
    config_dir = edison_dir / "config"
    config_dir.mkdir()

    # Create project config YAML
    (config_dir / "project.yaml").write_text(
        "scanRoots:\n  - ~/projects\n"
        "displayName: Test Project\n"
        "exposureMode: localhost\n"
        "realtime:\n  pollingIntervalMs: 5000\n"
    )

    # Create packs directory
    packs_dir = edison_dir / "packs"
    packs_dir.mkdir()

    # Create .project directory
    project_dir = project_path / ".project"
    project_dir.mkdir()
    (project_dir / "tasks").mkdir()
    (project_dir / "sessions").mkdir()

    # Create .git directory
    git_dir = project_path / ".git"
    git_dir.mkdir()

    return project_path


@pytest.fixture
def app_with_config_project(
    mock_edison_project_with_config: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    """Create app with mocked Edison project."""
    monkeypatch.setenv("SCAN_ROOTS", str(mock_edison_project_with_config.parent))
    monkeypatch.setenv("PIN_STORAGE_PATH", str(tmp_path / "pins.json"))
    monkeypatch.setenv("SETTINGS_FILE", str(tmp_path / "settings.json"))

    # Clear settings cache
    from core.settings import get_settings

    get_settings.cache_clear()

    app = create_app()
    return TestClient(app)


def get_project_id(client: TestClient) -> str:
    """Helper to get the first project ID."""
    response = client.get("/api/v1/projects")
    project_id: str = response.json()["items"][0]["projectId"]
    return project_id


class TestGetProjectConfig:
    """Tests for GET /projects/{projectId}/config endpoint."""

    def test_get_config_returns_200(self, app_with_config_project: TestClient) -> None:
        """Should return 200 OK for existing project."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.get(f"/api/v1/projects/{project_id}/config")
        assert response.status_code == 200

    def test_get_config_returns_project_id(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return projectId in response."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.get(f"/api/v1/projects/{project_id}/config")
        data = response.json()

        assert "projectId" in data
        assert data["projectId"] == project_id

    def test_get_config_returns_active_packs(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return activePacks array."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.get(f"/api/v1/projects/{project_id}/config")
        data = response.json()

        assert "activePacks" in data
        assert isinstance(data["activePacks"], list)

    def test_get_config_returns_config_object(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return config object with settings."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.get(f"/api/v1/projects/{project_id}/config")
        data = response.json()

        assert "config" in data
        assert isinstance(data["config"], dict)

    def test_get_config_includes_scan_roots(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should include scanRoots in config."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.get(f"/api/v1/projects/{project_id}/config")
        data = response.json()

        assert "scanRoots" in data["config"]

    def test_get_config_returns_404_for_unknown_project(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return 404 for unknown project."""
        response = app_with_config_project.get("/api/v1/projects/unknown-id/config")
        assert response.status_code == 404


class TestListPacks:
    """Tests for GET /projects/{projectId}/packs endpoint."""

    def test_list_packs_returns_200(self, app_with_config_project: TestClient) -> None:
        """Should return 200 OK."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.get(f"/api/v1/projects/{project_id}/packs")
        assert response.status_code == 200

    def test_list_packs_returns_items_array(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return items array."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.get(f"/api/v1/projects/{project_id}/packs")
        data = response.json()

        assert "items" in data
        assert isinstance(data["items"], list)

    def test_list_packs_returns_total(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return total count."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.get(f"/api/v1/projects/{project_id}/packs")
        data = response.json()

        assert "total" in data
        assert isinstance(data["total"], int)

    def test_list_packs_item_has_pack_id(
        self, app_with_config_project: TestClient, mock_edison_project_with_config: Path
    ) -> None:
        """Pack items should have packId field."""
        # Add a mock pack to the project
        packs_dir = mock_edison_project_with_config / ".edison" / "packs"
        pack_dir = packs_dir / "python"
        pack_dir.mkdir()
        (pack_dir / "pack.yaml").write_text(
            "name: Python Pack\ndescription: Python development configuration\n"
        )

        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.get(f"/api/v1/projects/{project_id}/packs")
        data = response.json()

        if data["items"]:
            assert "packId" in data["items"][0]

    def test_list_packs_item_has_name(
        self, app_with_config_project: TestClient, mock_edison_project_with_config: Path
    ) -> None:
        """Pack items should have name field."""
        packs_dir = mock_edison_project_with_config / ".edison" / "packs"
        pack_dir = packs_dir / "python"
        pack_dir.mkdir(exist_ok=True)
        (pack_dir / "pack.yaml").write_text(
            "name: Python Pack\ndescription: Python development configuration\n"
        )

        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.get(f"/api/v1/projects/{project_id}/packs")
        data = response.json()

        if data["items"]:
            assert "name" in data["items"][0]

    def test_list_packs_item_has_enabled(
        self, app_with_config_project: TestClient, mock_edison_project_with_config: Path
    ) -> None:
        """Pack items should have enabled field."""
        packs_dir = mock_edison_project_with_config / ".edison" / "packs"
        pack_dir = packs_dir / "python"
        pack_dir.mkdir(exist_ok=True)
        (pack_dir / "pack.yaml").write_text(
            "name: Python Pack\ndescription: Python development configuration\n"
        )

        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.get(f"/api/v1/projects/{project_id}/packs")
        data = response.json()

        if data["items"]:
            assert "enabled" in data["items"][0]

    def test_list_packs_item_has_source(
        self, app_with_config_project: TestClient, mock_edison_project_with_config: Path
    ) -> None:
        """Pack items should have source field (core/project)."""
        packs_dir = mock_edison_project_with_config / ".edison" / "packs"
        pack_dir = packs_dir / "python"
        pack_dir.mkdir(exist_ok=True)
        (pack_dir / "pack.yaml").write_text(
            "name: Python Pack\ndescription: Python development configuration\n"
        )

        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.get(f"/api/v1/projects/{project_id}/packs")
        data = response.json()

        if data["items"]:
            assert "source" in data["items"][0]

    def test_list_packs_returns_404_for_unknown_project(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return 404 for unknown project."""
        response = app_with_config_project.get("/api/v1/projects/unknown-id/packs")
        assert response.status_code == 404


class TestGetPackDetail:
    """Tests for GET /projects/{projectId}/packs/{packId} endpoint."""

    def test_get_pack_returns_200(
        self, app_with_config_project: TestClient, mock_edison_project_with_config: Path
    ) -> None:
        """Should return 200 for existing pack."""
        # Create a pack
        packs_dir = mock_edison_project_with_config / ".edison" / "packs"
        pack_dir = packs_dir / "python"
        pack_dir.mkdir(exist_ok=True)
        (pack_dir / "pack.yaml").write_text(
            "name: Python Pack\ndescription: Python development configuration\n"
        )

        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.get(
            f"/api/v1/projects/{project_id}/packs/python"
        )
        assert response.status_code == 200

    def test_get_pack_returns_pack_id(
        self, app_with_config_project: TestClient, mock_edison_project_with_config: Path
    ) -> None:
        """Should return packId in response."""
        packs_dir = mock_edison_project_with_config / ".edison" / "packs"
        pack_dir = packs_dir / "python"
        pack_dir.mkdir(exist_ok=True)
        (pack_dir / "pack.yaml").write_text(
            "name: Python Pack\ndescription: Python development configuration\n"
        )

        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.get(
            f"/api/v1/projects/{project_id}/packs/python"
        )
        data = response.json()

        assert "packId" in data
        assert data["packId"] == "python"

    def test_get_pack_returns_name(
        self, app_with_config_project: TestClient, mock_edison_project_with_config: Path
    ) -> None:
        """Should return name in response."""
        packs_dir = mock_edison_project_with_config / ".edison" / "packs"
        pack_dir = packs_dir / "python"
        pack_dir.mkdir(exist_ok=True)
        (pack_dir / "pack.yaml").write_text(
            "name: Python Pack\ndescription: Python development configuration\n"
        )

        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.get(
            f"/api/v1/projects/{project_id}/packs/python"
        )
        data = response.json()

        assert "name" in data
        assert data["name"] == "Python Pack"

    def test_get_pack_returns_description(
        self, app_with_config_project: TestClient, mock_edison_project_with_config: Path
    ) -> None:
        """Should return description in response."""
        packs_dir = mock_edison_project_with_config / ".edison" / "packs"
        pack_dir = packs_dir / "python"
        pack_dir.mkdir(exist_ok=True)
        (pack_dir / "pack.yaml").write_text(
            "name: Python Pack\ndescription: Python development configuration\n"
        )

        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.get(
            f"/api/v1/projects/{project_id}/packs/python"
        )
        data = response.json()

        assert "description" in data

    def test_get_pack_returns_config(
        self, app_with_config_project: TestClient, mock_edison_project_with_config: Path
    ) -> None:
        """Should return config object in response."""
        packs_dir = mock_edison_project_with_config / ".edison" / "packs"
        pack_dir = packs_dir / "python"
        pack_dir.mkdir(exist_ok=True)
        (pack_dir / "pack.yaml").write_text(
            "name: Python Pack\ndescription: Python development configuration\n"
            "config:\n  pythonVersion: '3.11'\n"
        )

        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.get(
            f"/api/v1/projects/{project_id}/packs/python"
        )
        data = response.json()

        assert "config" in data

    def test_get_pack_returns_404_for_unknown_pack(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return 404 for unknown pack."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.get(
            f"/api/v1/projects/{project_id}/packs/nonexistent-pack"
        )
        assert response.status_code == 404

    def test_get_pack_returns_404_for_unknown_project(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return 404 for unknown project."""
        response = app_with_config_project.get(
            "/api/v1/projects/unknown-id/packs/python"
        )
        assert response.status_code == 404


class TestConfigPreview:
    """Tests for POST /projects/{projectId}/config/preview endpoint."""

    def test_preview_returns_200_for_valid_field(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return 200 for allowlisted field."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.post(
            f"/api/v1/projects/{project_id}/config/preview",
            json={"field": "scanRoots", "value": ["~/projects", "~/work"]},
        )
        assert response.status_code == 200

    def test_preview_returns_valid_true_for_allowed_field(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return valid=true for allowed field."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.post(
            f"/api/v1/projects/{project_id}/config/preview",
            json={"field": "displayName", "value": "New Name"},
        )
        data = response.json()

        assert "valid" in data
        assert data["valid"] is True

    def test_preview_returns_current_and_new_values(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return preview with currentValue and newValue."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.post(
            f"/api/v1/projects/{project_id}/config/preview",
            json={"field": "displayName", "value": "New Name"},
        )
        data = response.json()

        assert "preview" in data
        assert "field" in data["preview"]
        assert "currentValue" in data["preview"]
        assert "newValue" in data["preview"]

    def test_preview_returns_valid_false_for_disallowed_field(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return valid=false for disallowed field."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.post(
            f"/api/v1/projects/{project_id}/config/preview",
            json={"field": "constitutions", "value": "malicious"},
        )
        data = response.json()

        assert "valid" in data
        assert data["valid"] is False

    def test_preview_returns_reason_for_disallowed_field(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return reason when field is disallowed."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.post(
            f"/api/v1/projects/{project_id}/config/preview",
            json={"field": "constitutions", "value": "malicious"},
        )
        data = response.json()

        assert "reason" in data
        assert (
            "not editable" in data["reason"].lower()
            or "not allowed" in data["reason"].lower()
        )

    def test_preview_returns_warnings_list(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return warnings array (may be empty)."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.post(
            f"/api/v1/projects/{project_id}/config/preview",
            json={"field": "displayName", "value": "New Name"},
        )
        data = response.json()

        assert "warnings" in data
        assert isinstance(data["warnings"], list)

    def test_preview_allows_exposure_mode(
        self, app_with_config_project: TestClient
    ) -> None:
        """exposureMode should be in the allowlist."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.post(
            f"/api/v1/projects/{project_id}/config/preview",
            json={"field": "exposureMode", "value": "network"},
        )
        data = response.json()

        assert data["valid"] is True

    def test_preview_allows_realtime_polling_interval(
        self, app_with_config_project: TestClient
    ) -> None:
        """realtime.pollingIntervalMs should be in the allowlist."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.post(
            f"/api/v1/projects/{project_id}/config/preview",
            json={"field": "realtime.pollingIntervalMs", "value": 3000},
        )
        data = response.json()

        assert data["valid"] is True

    def test_preview_disallows_pack_yaml_changes(
        self, app_with_config_project: TestClient
    ) -> None:
        """Direct pack YAML changes should be declined."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.post(
            f"/api/v1/projects/{project_id}/config/preview",
            json={"field": "packs.python.config", "value": {}},
        )
        data = response.json()

        assert data["valid"] is False

    def test_preview_disallows_credentials(
        self, app_with_config_project: TestClient
    ) -> None:
        """Credential modifications should be declined."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.post(
            f"/api/v1/projects/{project_id}/config/preview",
            json={"field": "credentials", "value": {"apiKey": "secret"}},
        )
        data = response.json()

        assert data["valid"] is False

    def test_preview_returns_404_for_unknown_project(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return 404 for unknown project."""
        response = app_with_config_project.post(
            "/api/v1/projects/unknown-id/config/preview",
            json={"field": "displayName", "value": "New Name"},
        )
        assert response.status_code == 404


class TestConfigApply:
    """Tests for POST /projects/{projectId}/config endpoint."""

    def test_apply_returns_200_for_valid_edit(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return 200 for confirmed valid edit."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.post(
            f"/api/v1/projects/{project_id}/config",
            json={"field": "displayName", "value": "New Name", "confirmed": True},
        )
        assert response.status_code == 200

    def test_apply_returns_success_true(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return success=true on successful apply."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.post(
            f"/api/v1/projects/{project_id}/config",
            json={"field": "displayName", "value": "New Name", "confirmed": True},
        )
        data = response.json()

        assert "success" in data
        assert data["success"] is True

    def test_apply_returns_audit_entry_id(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return auditEntryId for tracking."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.post(
            f"/api/v1/projects/{project_id}/config",
            json={"field": "displayName", "value": "New Name", "confirmed": True},
        )
        data = response.json()

        assert "auditEntryId" in data

    def test_apply_returns_backup_path(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return backupPath for rollback."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.post(
            f"/api/v1/projects/{project_id}/config",
            json={"field": "displayName", "value": "New Name", "confirmed": True},
        )
        data = response.json()

        assert "backupPath" in data

    def test_apply_requires_confirmed_flag(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should require confirmed=true to apply."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.post(
            f"/api/v1/projects/{project_id}/config",
            json={"field": "displayName", "value": "New Name", "confirmed": False},
        )
        # Either 400 or response with success=false
        data = response.json()
        if response.status_code == 200:
            assert data.get("success") is False

    def test_apply_rejects_disallowed_field(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should reject disallowed fields even with confirmed=true."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.post(
            f"/api/v1/projects/{project_id}/config",
            json={"field": "constitutions", "value": "malicious", "confirmed": True},
        )
        # Should return 400
        assert response.status_code == 400

    def test_apply_persists_change(self, app_with_config_project: TestClient) -> None:
        """Applied changes should be persisted."""
        project_id = get_project_id(app_with_config_project)

        # Apply change
        app_with_config_project.post(
            f"/api/v1/projects/{project_id}/config",
            json={"field": "displayName", "value": "Persisted Name", "confirmed": True},
        )

        # Verify change was persisted by reading config
        response = app_with_config_project.get(f"/api/v1/projects/{project_id}/config")
        data = response.json()

        # The displayName should be in the config
        assert data["config"].get("displayName") == "Persisted Name"

    def test_apply_returns_404_for_unknown_project(
        self, app_with_config_project: TestClient
    ) -> None:
        """Should return 404 for unknown project."""
        response = app_with_config_project.post(
            "/api/v1/projects/unknown-id/config",
            json={"field": "displayName", "value": "New Name", "confirmed": True},
        )
        assert response.status_code == 404


class TestConfigAllowlist:
    """Tests verifying the config edit allowlist."""

    ALLOWED_FIELDS = [
        "scanRoots",
        "displayName",
        "exposureMode",
        "realtime.pollingIntervalMs",
    ]

    DISALLOWED_FIELDS = [
        "constitutions",
        "credentials",
        "packs.python.config",
        "apiKeys",
        "secrets",
    ]

    @pytest.mark.parametrize("field", ALLOWED_FIELDS)
    def test_allowed_fields_pass_preview(
        self, app_with_config_project: TestClient, field: str
    ) -> None:
        """All allowlisted fields should pass preview validation."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.post(
            f"/api/v1/projects/{project_id}/config/preview",
            json={"field": field, "value": "test-value"},
        )
        data = response.json()

        assert data["valid"] is True, f"Field '{field}' should be allowed"

    @pytest.mark.parametrize("field", DISALLOWED_FIELDS)
    def test_disallowed_fields_fail_preview(
        self, app_with_config_project: TestClient, field: str
    ) -> None:
        """All disallowed fields should fail preview validation."""
        project_id = get_project_id(app_with_config_project)
        response = app_with_config_project.post(
            f"/api/v1/projects/{project_id}/config/preview",
            json={"field": field, "value": "test-value"},
        )
        data = response.json()

        assert data["valid"] is False, f"Field '{field}' should be disallowed"


class TestConfigSchemas:
    """Tests for config-related Pydantic schemas."""

    def test_project_config_response_schema(self) -> None:
        """Should validate ProjectConfigResponse schema."""
        from api.schemas.config import ProjectConfigResponse

        response = ProjectConfigResponse(
            project_id="test-id",
            active_packs=["python", "typescript"],
            config={"scanRoots": ["~/projects"]},
        )

        assert response.project_id == "test-id"
        assert response.active_packs == ["python", "typescript"]

    def test_pack_list_item_schema(self) -> None:
        """Should validate PackListItem schema."""
        from api.schemas.config import PackListItem

        item = PackListItem(
            pack_id="python",
            name="Python Pack",
            description="Python development configuration",
            enabled=True,
            source="core",
        )

        assert item.pack_id == "python"

    def test_pack_detail_schema(self) -> None:
        """Should validate PackDetail schema."""
        from api.schemas.config import PackDetail

        detail = PackDetail(
            pack_id="python",
            name="Python Pack",
            description="Python development configuration",
            enabled=True,
            config={"pythonVersion": "3.11"},
            source="core",
        )

        assert detail.config == {"pythonVersion": "3.11"}

    def test_config_preview_request_schema(self) -> None:
        """Should validate ConfigPreviewRequest schema."""
        from api.schemas.config import ConfigPreviewRequest

        request = ConfigPreviewRequest(field="scanRoots", value=["~/projects"])

        assert request.field == "scanRoots"

    def test_config_preview_response_schema(self) -> None:
        """Should validate ConfigPreviewResponse schema."""
        from api.schemas.config import ConfigPreviewResponse, ConfigPreview

        response = ConfigPreviewResponse(
            valid=True,
            warnings=[],
            preview=ConfigPreview(
                field="scanRoots",
                current_value=["~/projects"],
                new_value=["~/projects", "~/work"],
            ),
        )

        assert response.valid is True

    def test_config_apply_request_schema(self) -> None:
        """Should validate ConfigApplyRequest schema."""
        from api.schemas.config import ConfigApplyRequest

        request = ConfigApplyRequest(
            field="scanRoots", value=["~/projects"], confirmed=True
        )

        assert request.confirmed is True

    def test_config_apply_response_schema(self) -> None:
        """Should validate ConfigApplyResponse schema."""
        from api.schemas.config import ConfigApplyResponse

        response = ConfigApplyResponse(
            success=True,
            audit_entry_id="audit-123",
            backup_path=".edison/.config-backup/2026-01-07.yaml",
        )

        assert response.success is True
