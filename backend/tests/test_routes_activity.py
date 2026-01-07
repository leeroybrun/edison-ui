"""Tests for activity API routes (T078).

Tests activity and audit endpoints return real data from JSONL logs.
"""

from __future__ import annotations

import json
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


class TestActivityEndpoints:
    """Test cases for activity endpoints."""

    @pytest.fixture
    def project_root(self, tmp_path: Path) -> Path:
        """Create a temporary project with audit logs."""
        # Create Edison structure
        project = tmp_path / "test-project"
        project.mkdir()
        (project / ".project").mkdir()
        (project / ".project" / "logs" / "edison").mkdir(parents=True)

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

        audit_path = project / ".project" / "logs" / "edison" / "audit.jsonl"
        with open(audit_path, "w") as f:
            for entry in audit_entries:
                f.write(json.dumps(entry) + "\n")

        return project

    @pytest.fixture
    def client(self, project_root: Path) -> Generator[TestClient, None, None]:
        """Create a test client with mocked project discovery."""
        from main import app
        from services.project_discovery import DiscoveredProject

        # Mock the project discovery to return our test project
        mock_project = DiscoveredProject(
            project_id="test-project",
            name="test-project",
            path=str(project_root),
        )

        def mock_get_project_by_id(project_id: str) -> DiscoveredProject | None:
            if project_id == "test-project":
                return mock_project
            return None

        with patch(
            "api.routes.activity.get_discovery_service"
        ) as mock_discovery:
            mock_service = mock_discovery.return_value
            mock_service.get_project_by_id = mock_get_project_by_id
            yield TestClient(app)

    def test_get_activity_returns_items(
        self, client: TestClient, project_root: Path
    ) -> None:
        """GET /projects/{id}/activity should return activity items."""
        response = client.get("/api/v1/projects/test-project/activity")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "hasMore" in data
        # Should have 1 activity item (from cli.invocation.end)
        assert len(data["items"]) == 1
        assert data["items"][0]["eventType"] == "session.create"

    def test_get_audit_returns_items(
        self, client: TestClient, project_root: Path
    ) -> None:
        """GET /projects/{id}/audit should return raw audit events."""
        response = client.get("/api/v1/projects/test-project/audit")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "hasMore" in data
        # Should have 2 audit events (start and end)
        assert len(data["items"]) == 2

    def test_activity_filter_by_session(
        self, client: TestClient, project_root: Path
    ) -> None:
        """Activity should filter by sessionId."""
        response = client.get(
            "/api/v1/projects/test-project/activity?sessionId=session-1"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1

        # Filter by non-existent session
        response = client.get(
            "/api/v1/projects/test-project/activity?sessionId=nonexistent"
        )
        data = response.json()
        assert len(data["items"]) == 0

    def test_audit_filter_by_invocation(
        self, client: TestClient, project_root: Path
    ) -> None:
        """Audit should filter by invocationId."""
        response = client.get(
            "/api/v1/projects/test-project/audit?invocationId=inv-001"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2

    def test_activity_limit(self, client: TestClient, project_root: Path) -> None:
        """Activity should respect limit parameter."""
        response = client.get("/api/v1/projects/test-project/activity?limit=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 1

    def test_project_not_found(self, client: TestClient) -> None:
        """Should return 404 for unknown project."""
        response = client.get("/api/v1/projects/nonexistent/activity")
        assert response.status_code == 404
