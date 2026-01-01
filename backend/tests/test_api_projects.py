"""Tests for project discovery/list/detail endpoints (T010).

RED Phase: These tests MUST fail initially as the endpoints don't exist yet.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.fixture
def mock_edison_project(tmp_path: Path) -> Path:
    """Create a mock Edison project structure."""
    project_path = tmp_path / "test-project"
    project_path.mkdir()

    # Create .edison directory (marks it as an Edison project)
    edison_dir = project_path / ".edison"
    edison_dir.mkdir()

    # Create .project directory with tasks/sessions/qa
    project_dir = project_path / ".project"
    project_dir.mkdir()

    # Create task directories
    tasks_dir = project_dir / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "todo").mkdir()
    (tasks_dir / "wip").mkdir()
    (tasks_dir / "done").mkdir()
    (tasks_dir / "validated").mkdir()

    # Add some mock tasks
    (tasks_dir / "todo" / "T001.md").write_text("---\nid: T001\ntitle: Test Task 1\n---\n# Test Task 1")
    (tasks_dir / "wip" / "T002.md").write_text("---\nid: T002\ntitle: Test Task 2\n---\n# Test Task 2")

    # Create session directories
    sessions_dir = project_dir / "sessions"
    sessions_dir.mkdir()
    (sessions_dir / "active").mkdir()

    # Add a mock session
    session_dir = sessions_dir / "active" / "test-session"
    session_dir.mkdir()
    session_json = {
        "id": "test-session",
        "state": "active",
        "phase": "implementation",
        "meta": {
            "sessionId": "test-session",
            "createdAt": "2025-12-27T10:00:00Z",
            "lastActive": "2025-12-27T10:00:00Z"
        }
    }
    (session_dir / "session.json").write_text(json.dumps(session_json))

    # Create QA directories
    qa_dir = project_dir / "qa"
    qa_dir.mkdir()
    (qa_dir / "todo").mkdir()
    (qa_dir / "wip").mkdir()
    (qa_dir / "done").mkdir()
    (qa_dir / "validated").mkdir()

    # Add a mock QA
    (qa_dir / "todo" / "QA-T001.md").write_text("---\nid: QA-T001\ntask_id: T001\n---\n# QA for T001")

    # Create .git directory (marks it as a git repo)
    git_dir = project_path / ".git"
    git_dir.mkdir()

    return project_path


@pytest.fixture
def mock_non_edison_project(tmp_path: Path) -> Path:
    """Create a non-Edison project (just a git repo without .edison)."""
    project_path = tmp_path / "non-edison-project"
    project_path.mkdir()

    # Only .git, no .edison
    git_dir = project_path / ".git"
    git_dir.mkdir()

    return project_path


@pytest.fixture
def mock_scan_root(
    tmp_path: Path, mock_edison_project: Path, mock_non_edison_project: Path
) -> Path:
    """Create a scan root with multiple projects."""
    # The projects are already in tmp_path subdirectories
    # Return tmp_path as the scan root
    return tmp_path


@pytest.fixture
def app_with_scan_root(mock_scan_root: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create app with mocked scan roots."""
    # Set environment variable for scan roots
    monkeypatch.setenv("SCAN_ROOTS", str(mock_scan_root))

    # Clear settings cache to pick up new env
    from core.settings import get_settings
    get_settings.cache_clear()

    app = create_app()
    return TestClient(app)


class TestListProjects:
    """Tests for GET /projects endpoint."""

    def test_list_projects_returns_200(self, app_with_scan_root: TestClient) -> None:
        """Should return 200 OK with list of projects."""
        response = app_with_scan_root.get("/api/v1/projects")
        assert response.status_code == 200

    def test_list_projects_returns_items_array(self, app_with_scan_root: TestClient) -> None:
        """Should return items array in response."""
        response = app_with_scan_root.get("/api/v1/projects")
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_list_projects_includes_edison_projects_only(
        self, app_with_scan_root: TestClient
    ) -> None:
        """Should only include Edison projects (those with .edison directory)."""
        response = app_with_scan_root.get("/api/v1/projects")
        data = response.json()

        # Should find the Edison project but not the non-Edison one
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "test-project"

    def test_list_projects_includes_health_counts(
        self, app_with_scan_root: TestClient
    ) -> None:
        """Should include health counts (task/session/qa counts)."""
        response = app_with_scan_root.get("/api/v1/projects")
        data = response.json()

        project = data["items"][0]
        assert "health" in project
        assert "taskCount" in project["health"]
        assert "sessionCount" in project["health"]
        assert "qaCount" in project["health"]
        assert "activeCount" in project["health"]

    def test_list_projects_includes_project_id(
        self, app_with_scan_root: TestClient
    ) -> None:
        """Should include a stable projectId."""
        response = app_with_scan_root.get("/api/v1/projects")
        data = response.json()

        project = data["items"][0]
        assert "projectId" in project
        assert project["projectId"]  # Not empty

    def test_list_projects_includes_pagination_info(
        self, app_with_scan_root: TestClient
    ) -> None:
        """Should include pagination info (total, limit, offset)."""
        response = app_with_scan_root.get("/api/v1/projects")
        data = response.json()

        assert "total" in data
        assert "limit" in data
        assert "offset" in data

    def test_list_projects_pagination_limit(
        self, app_with_scan_root: TestClient
    ) -> None:
        """Should respect limit parameter."""
        response = app_with_scan_root.get("/api/v1/projects?limit=5")
        data = response.json()

        assert data["limit"] == 5

    def test_list_projects_pagination_offset(
        self, app_with_scan_root: TestClient
    ) -> None:
        """Should respect offset parameter."""
        response = app_with_scan_root.get("/api/v1/projects?offset=10")
        data = response.json()

        assert data["offset"] == 10

    def test_list_projects_filter_by_pinned(
        self, app_with_scan_root: TestClient
    ) -> None:
        """Should filter by pinned status."""
        response = app_with_scan_root.get("/api/v1/projects?pinned=true")
        assert response.status_code == 200
        data = response.json()
        # All returned projects should be pinned
        for project in data["items"]:
            assert project.get("pinned", False) is True

    def test_list_projects_has_git_field(
        self, app_with_scan_root: TestClient
    ) -> None:
        """Should include hasGit field."""
        response = app_with_scan_root.get("/api/v1/projects")
        data = response.json()

        project = data["items"][0]
        assert "hasGit" in project
        assert project["hasGit"] is True  # Our mock project has .git

    def test_list_projects_redacts_path(
        self, app_with_scan_root: TestClient
    ) -> None:
        """Should redact the full path (per security requirements)."""
        response = app_with_scan_root.get("/api/v1/projects")
        data = response.json()

        project = data["items"][0]
        assert "path" in project
        # Path should be redacted (not contain full system path)
        # It should show relative or redacted path
        assert not project["path"].startswith("/tmp") or "[REDACTED" in project["path"]


class TestGetProjectDetail:
    """Tests for GET /projects/{projectId} endpoint."""

    def test_get_project_returns_200(self, app_with_scan_root: TestClient) -> None:
        """Should return 200 for existing project."""
        # First get the project ID from list
        list_response = app_with_scan_root.get("/api/v1/projects")
        project_id = list_response.json()["items"][0]["projectId"]

        response = app_with_scan_root.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200

    def test_get_project_returns_404_for_unknown(
        self, app_with_scan_root: TestClient
    ) -> None:
        """Should return 404 for unknown project."""
        response = app_with_scan_root.get("/api/v1/projects/unknown-project-id")
        assert response.status_code == 404

    def test_get_project_includes_all_fields(
        self, app_with_scan_root: TestClient
    ) -> None:
        """Should include all detail fields."""
        list_response = app_with_scan_root.get("/api/v1/projects")
        project_id = list_response.json()["items"][0]["projectId"]

        response = app_with_scan_root.get(f"/api/v1/projects/{project_id}")
        data = response.json()

        # Check all required fields per api.md contract
        assert "projectId" in data
        assert "path" in data
        assert "name" in data
        assert "pinned" in data
        assert "health" in data
        assert "lastActivityAt" in data
        assert "hasGit" in data
        assert "errors" in data
        assert "config" in data

    def test_get_project_config_includes_scan_roots(
        self, app_with_scan_root: TestClient
    ) -> None:
        """Should include config with scanRoots."""
        list_response = app_with_scan_root.get("/api/v1/projects")
        project_id = list_response.json()["items"][0]["projectId"]

        response = app_with_scan_root.get(f"/api/v1/projects/{project_id}")
        data = response.json()

        assert "config" in data
        assert "scanRoots" in data["config"]


class TestPinProject:
    """Tests for PATCH /projects/{projectId}/pin endpoint."""

    def test_pin_project_returns_200(self, app_with_scan_root: TestClient) -> None:
        """Should return 200 on success."""
        list_response = app_with_scan_root.get("/api/v1/projects")
        project_id = list_response.json()["items"][0]["projectId"]

        response = app_with_scan_root.patch(
            f"/api/v1/projects/{project_id}/pin",
            json={"pinned": True}
        )
        assert response.status_code == 200

    def test_pin_project_returns_updated_status(
        self, app_with_scan_root: TestClient
    ) -> None:
        """Should return updated pin status."""
        list_response = app_with_scan_root.get("/api/v1/projects")
        project_id = list_response.json()["items"][0]["projectId"]

        response = app_with_scan_root.patch(
            f"/api/v1/projects/{project_id}/pin",
            json={"pinned": True}
        )
        data = response.json()

        assert data["projectId"] == project_id
        assert data["pinned"] is True

    def test_unpin_project(self, app_with_scan_root: TestClient) -> None:
        """Should be able to unpin a project."""
        list_response = app_with_scan_root.get("/api/v1/projects")
        project_id = list_response.json()["items"][0]["projectId"]

        # First pin
        app_with_scan_root.patch(
            f"/api/v1/projects/{project_id}/pin",
            json={"pinned": True}
        )

        # Then unpin
        response = app_with_scan_root.patch(
            f"/api/v1/projects/{project_id}/pin",
            json={"pinned": False}
        )
        data = response.json()

        assert data["pinned"] is False

    def test_pin_project_returns_404_for_unknown(
        self, app_with_scan_root: TestClient
    ) -> None:
        """Should return 404 for unknown project."""
        response = app_with_scan_root.patch(
            "/api/v1/projects/unknown-project-id/pin",
            json={"pinned": True}
        )
        assert response.status_code == 404


class TestProjectDiscoveryService:
    """Tests for the project discovery service."""

    def test_discovers_edison_projects(self, mock_scan_root: Path) -> None:
        """Should discover Edison projects in scan roots."""
        from services.project_discovery import ProjectDiscoveryService

        service = ProjectDiscoveryService(scan_roots=[str(mock_scan_root)])
        projects = service.discover_projects()

        assert len(projects) == 1
        assert projects[0].name == "test-project"

    def test_ignores_non_edison_projects(self, mock_scan_root: Path) -> None:
        """Should not include non-Edison projects."""
        from services.project_discovery import ProjectDiscoveryService

        service = ProjectDiscoveryService(scan_roots=[str(mock_scan_root)])
        projects = service.discover_projects()

        project_names = [p.name for p in projects]
        assert "non-edison-project" not in project_names

    def test_generates_stable_project_id(self, mock_edison_project: Path) -> None:
        """Should generate stable project ID from path."""
        from services.project_discovery import ProjectDiscoveryService

        service = ProjectDiscoveryService(scan_roots=[str(mock_edison_project.parent)])
        projects = service.discover_projects()

        # Get same project twice - ID should be stable
        projects2 = service.discover_projects()

        assert projects[0].project_id == projects2[0].project_id

    def test_counts_tasks_by_state(self, mock_edison_project: Path) -> None:
        """Should count tasks in each state."""
        from services.project_discovery import ProjectDiscoveryService

        service = ProjectDiscoveryService(scan_roots=[str(mock_edison_project.parent)])
        projects = service.discover_projects()

        health = projects[0].health
        assert health.task_count == 2  # 1 in todo, 1 in wip

    def test_counts_active_sessions(self, mock_edison_project: Path) -> None:
        """Should count active sessions."""
        from services.project_discovery import ProjectDiscoveryService

        service = ProjectDiscoveryService(scan_roots=[str(mock_edison_project.parent)])
        projects = service.discover_projects()

        health = projects[0].health
        assert health.session_count == 1
        assert health.active_count == 1


class TestProjectSchemas:
    """Tests for project-related Pydantic schemas."""

    def test_project_health_schema(self) -> None:
        """Should validate ProjectHealth schema."""
        from api.schemas.projects import ProjectHealth

        health = ProjectHealth(
            task_count=10,
            session_count=2,
            qa_count=5,
            active_count=1
        )

        assert health.task_count == 10

    def test_project_list_item_schema(self) -> None:
        """Should validate ProjectListItem schema."""
        from api.schemas.projects import ProjectListItem, ProjectHealth

        item = ProjectListItem(
            project_id="test-id",
            path="~/projects/test",
            name="test",
            pinned=False,
            health=ProjectHealth(
                task_count=0,
                session_count=0,
                qa_count=0,
                active_count=0
            ),
            last_activity_at="2025-12-27T10:00:00Z",
            has_git=True,
            errors=[]
        )

        assert item.project_id == "test-id"

    def test_project_list_response_schema(self) -> None:
        """Should validate ProjectListResponse schema."""
        from api.schemas.projects import ProjectListResponse

        response = ProjectListResponse(
            items=[],
            total=0,
            limit=100,
            offset=0
        )

        assert response.total == 0
