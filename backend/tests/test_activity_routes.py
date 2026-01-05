"""Tests for activity routes (T044).

Tests for GET /projects/{projectId}/activity and /audit endpoints.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def mock_edison_project(tmp_path: Path) -> Path:
    """Create a minimal mock Edison project for testing."""
    project_path = tmp_path / "test-project"
    project_path.mkdir()

    # Create .project directory to mark as Edison project
    project_dir = project_path / ".project"
    project_dir.mkdir()

    # Create minimal constitution file
    constitution = project_path / ".edison" / "_generated" / "constitutions"
    constitution.mkdir(parents=True)
    (constitution / "AGENTS.md").write_text("# Test Project\n")

    return project_path


@pytest.fixture
def client_with_project(
    mock_edison_project: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    """Create app with mocked scan roots pointing to test project."""
    monkeypatch.setenv("SCAN_ROOTS", str(mock_edison_project.parent))
    monkeypatch.setenv("PIN_STORAGE_PATH", str(tmp_path / "pins.json"))

    from core.settings import get_settings

    # Clear the settings cache to pick up new env vars
    get_settings.cache_clear()

    return TestClient(app)


@pytest.fixture
def project_id(client_with_project: TestClient) -> str:
    """Get the project ID from the mocked project."""
    response = client_with_project.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    assert data["items"], "Mock project should be discovered"
    return str(data["items"][0]["projectId"])


class TestActivityEndpoint:
    """Tests for GET /projects/{projectId}/activity endpoint."""

    def test_get_activity_returns_200(
        self, client_with_project: TestClient, project_id: str
    ) -> None:
        """Activity endpoint returns 200 for valid project."""
        response = client_with_project.get(f"/api/v1/projects/{project_id}/activity")
        assert response.status_code == 200

    def test_get_activity_returns_expected_schema(
        self, client_with_project: TestClient, project_id: str
    ) -> None:
        """Activity endpoint returns expected response schema."""
        response = client_with_project.get(f"/api/v1/projects/{project_id}/activity")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "hasMore" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["hasMore"], bool)

    def test_get_activity_with_filters(
        self, client_with_project: TestClient, project_id: str
    ) -> None:
        """Activity endpoint accepts filter parameters."""
        response = client_with_project.get(
            f"/api/v1/projects/{project_id}/activity",
            params={
                "sessionId": "test-session",
                "taskId": "T001",
                "eventType": "task_created",
                "since": "2024-01-01T00:00:00Z",
                "limit": 25,
            },
        )
        assert response.status_code == 200

    def test_get_activity_not_found_for_invalid_project(
        self, client_with_project: TestClient
    ) -> None:
        """Activity endpoint returns 404 for invalid project."""
        response = client_with_project.get(
            "/api/v1/projects/invalid-project-id/activity"
        )
        assert response.status_code == 404

    def test_get_activity_returns_empty_items_phase1(
        self, client_with_project: TestClient, project_id: str
    ) -> None:
        """Phase 1: Activity endpoint returns empty items for UI scaffolding."""
        response = client_with_project.get(f"/api/v1/projects/{project_id}/activity")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["hasMore"] is False


class TestAuditEndpoint:
    """Tests for GET /projects/{projectId}/audit endpoint."""

    def test_get_audit_returns_200(
        self, client_with_project: TestClient, project_id: str
    ) -> None:
        """Audit endpoint returns 200 for valid project."""
        response = client_with_project.get(f"/api/v1/projects/{project_id}/audit")
        assert response.status_code == 200

    def test_get_audit_returns_expected_schema(
        self, client_with_project: TestClient, project_id: str
    ) -> None:
        """Audit endpoint returns expected response schema."""
        response = client_with_project.get(f"/api/v1/projects/{project_id}/audit")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "hasMore" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["hasMore"], bool)

    def test_get_audit_with_filters(
        self, client_with_project: TestClient, project_id: str
    ) -> None:
        """Audit endpoint accepts filter parameters."""
        response = client_with_project.get(
            f"/api/v1/projects/{project_id}/audit",
            params={
                "sessionId": "test-session",
                "invocationId": "inv-123",
                "since": "2024-01-01T00:00:00Z",
                "limit": 25,
            },
        )
        assert response.status_code == 200

    def test_get_audit_not_found_for_invalid_project(
        self, client_with_project: TestClient
    ) -> None:
        """Audit endpoint returns 404 for invalid project."""
        response = client_with_project.get("/api/v1/projects/invalid-project-id/audit")
        assert response.status_code == 404

    def test_get_audit_returns_empty_items_phase1(
        self, client_with_project: TestClient, project_id: str
    ) -> None:
        """Phase 1: Audit endpoint returns empty items for UI scaffolding."""
        response = client_with_project.get(f"/api/v1/projects/{project_id}/audit")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["hasMore"] is False
