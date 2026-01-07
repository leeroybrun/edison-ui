"""Tests for activity API routes (T078).

Tests activity and audit endpoints return real data from JSONL logs.
Uses real file-based projects with monkeypatched environment variables
(NO MOCKS policy compliant).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.fixture
def edison_project_with_audit(tmp_path: Path) -> Path:
    """Create a temporary Edison project with audit logs."""
    project = tmp_path / "test-project"
    project.mkdir()

    # Create .edison directory (marks it as an Edison project)
    (project / ".edison").mkdir()

    # Create .project directory with required structure
    project_dir = project / ".project"
    project_dir.mkdir()

    # Create task directories (required for project discovery)
    tasks_dir = project_dir / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "todo").mkdir()
    (tasks_dir / "wip").mkdir()
    (tasks_dir / "done").mkdir()
    (tasks_dir / "validated").mkdir()

    # Create session directories
    sessions_dir = project_dir / "sessions"
    sessions_dir.mkdir()
    (sessions_dir / "active").mkdir()

    # Create QA directories
    qa_dir = project_dir / "qa"
    qa_dir.mkdir()
    (qa_dir / "todo").mkdir()
    (qa_dir / "wip").mkdir()
    (qa_dir / "done").mkdir()
    (qa_dir / "validated").mkdir()

    # Create Edison logs directory with audit JSONL
    logs_dir = project_dir / "logs" / "edison"
    logs_dir.mkdir(parents=True)

    # Create audit log with sample entries
    audit_entries = [
        {
            "ts": "2026-01-01T10:00:00Z",
            "event": "cli.invocation.start",
            "pid": 1000,
            "invocation_id": "inv-001",
            "session_id": "session-1",
            "task_id": None,
            "project_root": str(project),
            "command": "session create",
        },
        {
            "ts": "2026-01-01T10:00:05Z",
            "event": "cli.invocation.end",
            "pid": 1000,
            "invocation_id": "inv-001",
            "session_id": "session-1",
            "task_id": None,
            "project_root": str(project),
            "command": "session create",
            "exit_code": 0,
            "duration_ms": 5000,
        },
    ]

    audit_path = logs_dir / "audit.jsonl"
    with open(audit_path, "w") as f:
        for entry in audit_entries:
            f.write(json.dumps(entry) + "\n")

    return project


@pytest.fixture
def app_client(
    tmp_path: Path,
    edison_project_with_audit: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    """Create app with monkeypatched scan roots and pin storage."""
    # Set environment variables
    monkeypatch.setenv("SCAN_ROOTS", str(tmp_path))
    monkeypatch.setenv("PIN_STORAGE_PATH", str(tmp_path / "pins.json"))

    # Clear settings cache to pick up new env
    from core.settings import get_settings

    get_settings.cache_clear()

    app = create_app()
    return TestClient(app)


class TestActivityEndpoints:
    """Test cases for activity endpoints."""

    def test_get_activity_returns_items(
        self, app_client: TestClient, edison_project_with_audit: Path
    ) -> None:
        """GET /projects/{id}/activity should return activity items."""
        # Get the project ID (derived from path)
        from services.project_discovery import ProjectDiscoveryService

        service = ProjectDiscoveryService(
            scan_roots=[str(edison_project_with_audit.parent)]
        )
        projects = service.discover_projects()
        assert len(projects) == 1
        project_id = projects[0].project_id

        response = app_client.get(f"/api/v1/projects/{project_id}/activity")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "hasMore" in data
        # Should have 1 activity item (from cli.invocation.end)
        assert len(data["items"]) == 1
        assert data["items"][0]["eventType"] == "session.create"

    def test_get_audit_returns_items(
        self, app_client: TestClient, edison_project_with_audit: Path
    ) -> None:
        """GET /projects/{id}/audit should return raw audit events."""
        from services.project_discovery import ProjectDiscoveryService

        service = ProjectDiscoveryService(
            scan_roots=[str(edison_project_with_audit.parent)]
        )
        projects = service.discover_projects()
        project_id = projects[0].project_id

        response = app_client.get(f"/api/v1/projects/{project_id}/audit")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "hasMore" in data
        # Should have 2 audit events (start and end)
        assert len(data["items"]) == 2

    def test_activity_filter_by_session(
        self, app_client: TestClient, edison_project_with_audit: Path
    ) -> None:
        """Activity should filter by sessionId."""
        from services.project_discovery import ProjectDiscoveryService

        service = ProjectDiscoveryService(
            scan_roots=[str(edison_project_with_audit.parent)]
        )
        projects = service.discover_projects()
        project_id = projects[0].project_id

        response = app_client.get(
            f"/api/v1/projects/{project_id}/activity?sessionId=session-1"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1

        # Filter by non-existent session
        response = app_client.get(
            f"/api/v1/projects/{project_id}/activity?sessionId=nonexistent"
        )
        data = response.json()
        assert len(data["items"]) == 0

    def test_audit_filter_by_invocation(
        self, app_client: TestClient, edison_project_with_audit: Path
    ) -> None:
        """Audit should filter by invocationId."""
        from services.project_discovery import ProjectDiscoveryService

        service = ProjectDiscoveryService(
            scan_roots=[str(edison_project_with_audit.parent)]
        )
        projects = service.discover_projects()
        project_id = projects[0].project_id

        response = app_client.get(
            f"/api/v1/projects/{project_id}/audit?invocationId=inv-001"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2

    def test_activity_limit(
        self, app_client: TestClient, edison_project_with_audit: Path
    ) -> None:
        """Activity should respect limit parameter."""
        from services.project_discovery import ProjectDiscoveryService

        service = ProjectDiscoveryService(
            scan_roots=[str(edison_project_with_audit.parent)]
        )
        projects = service.discover_projects()
        project_id = projects[0].project_id

        response = app_client.get(f"/api/v1/projects/{project_id}/activity?limit=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 1

    def test_project_not_found(self, app_client: TestClient) -> None:
        """Should return 404 for unknown project."""
        response = app_client.get("/api/v1/projects/nonexistent/activity")
        assert response.status_code == 404
