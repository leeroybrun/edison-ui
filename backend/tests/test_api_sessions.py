"""Tests for sessions listing endpoint (T021).

RED Phase: These tests MUST fail initially as the endpoints don't exist yet.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.fixture
def mock_edison_project_with_sessions(tmp_path: Path) -> Path:
    """Create a mock Edison project with multiple sessions in different states."""
    project_path = tmp_path / "test-project"
    project_path.mkdir()

    # Create .edison directory (marks it as an Edison project)
    edison_dir = project_path / ".edison"
    edison_dir.mkdir()

    # Create .project directory with sessions
    project_dir = project_path / ".project"
    project_dir.mkdir()

    # Create session directories for different states
    sessions_dir = project_dir / "sessions"
    sessions_dir.mkdir()

    # Create state directories
    for state in ["draft", "active", "paused", "completed", "abandoned"]:
        (sessions_dir / state).mkdir()

    # Add an active session
    active_session_dir = sessions_dir / "active" / "session-active-1"
    active_session_dir.mkdir()
    active_session_json = {
        "id": "session-active-1",
        "state": "active",
        "phase": "implementation",
        "meta": {
            "sessionId": "session-active-1",
            "owner": "leeroy",
            "createdAt": "2025-12-27T10:00:00Z",
            "lastActive": "2025-12-27T12:00:00Z",
            "status": "working"
        },
        "git": {
            "branchName": "feature/foo",
            "baseBranch": "main"
        },
        "tasks": {"T001": "wip", "T002": "todo", "T003": "done"}
    }
    (active_session_dir / "session.json").write_text(json.dumps(active_session_json))

    # Add a draft session
    draft_session_dir = sessions_dir / "draft" / "session-draft-1"
    draft_session_dir.mkdir()
    draft_session_json = {
        "id": "session-draft-1",
        "state": "draft",
        "phase": "planning",
        "meta": {
            "sessionId": "session-draft-1",
            "createdAt": "2025-12-26T08:00:00Z",
            "lastActive": "2025-12-26T09:00:00Z"
        },
        "git": {
            "baseBranch": "main"
        }
    }
    (draft_session_dir / "session.json").write_text(json.dumps(draft_session_json))

    # Add a completed session
    completed_session_dir = sessions_dir / "completed" / "session-completed-1"
    completed_session_dir.mkdir()
    completed_session_json = {
        "id": "session-completed-1",
        "state": "completed",
        "phase": "qa",
        "meta": {
            "sessionId": "session-completed-1",
            "owner": "jenkins",
            "createdAt": "2025-12-20T10:00:00Z",
            "lastActive": "2025-12-22T15:00:00Z"
        },
        "git": {
            "branchName": "feature/bar",
            "baseBranch": "main"
        },
        "tasks": {"T010": "validated", "T011": "validated"}
    }
    (completed_session_dir / "session.json").write_text(json.dumps(completed_session_json))

    # Create .git directory (marks it as a git repo)
    git_dir = project_path / ".git"
    git_dir.mkdir()

    return project_path


@pytest.fixture
def app_with_sessions(
    mock_edison_project_with_sessions: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    """Create app with mocked scan roots for sessions tests."""
    scan_root = mock_edison_project_with_sessions.parent
    monkeypatch.setenv("SCAN_ROOTS", str(scan_root))
    monkeypatch.setenv("PIN_STORAGE_PATH", str(tmp_path / "pins.json"))

    # Clear settings cache to pick up new env
    from core.settings import get_settings
    get_settings.cache_clear()

    app = create_app()
    return TestClient(app)


@pytest.fixture
def project_id(app_with_sessions: TestClient) -> str:
    """Get the project ID from the discovered project."""
    response = app_with_sessions.get("/api/v1/projects")
    return str(response.json()["items"][0]["projectId"])


class TestListSessions:
    """Tests for GET /projects/{projectId}/sessions endpoint."""

    def test_list_sessions_returns_200(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return 200 OK with list of sessions."""
        response = app_with_sessions.get(f"/api/v1/projects/{project_id}/sessions")
        assert response.status_code == 200

    def test_list_sessions_returns_items_array(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return items array in response."""
        response = app_with_sessions.get(f"/api/v1/projects/{project_id}/sessions")
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_list_sessions_returns_all_sessions(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return all sessions from all states."""
        response = app_with_sessions.get(f"/api/v1/projects/{project_id}/sessions")
        data = response.json()

        # We created 3 sessions: active, draft, and completed
        assert len(data["items"]) == 3

    def test_list_sessions_includes_session_id(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should include sessionId for each session."""
        response = app_with_sessions.get(f"/api/v1/projects/{project_id}/sessions")
        data = response.json()

        for session in data["items"]:
            assert "sessionId" in session
            assert session["sessionId"]  # Not empty

    def test_list_sessions_includes_state(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should include state for each session."""
        response = app_with_sessions.get(f"/api/v1/projects/{project_id}/sessions")
        data = response.json()

        session_states = {s["sessionId"]: s["state"] for s in data["items"]}
        assert session_states["session-active-1"] == "active"
        assert session_states["session-draft-1"] == "draft"
        assert session_states["session-completed-1"] == "completed"

    def test_list_sessions_includes_phase(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should include phase for each session."""
        response = app_with_sessions.get(f"/api/v1/projects/{project_id}/sessions")
        data = response.json()

        for session in data["items"]:
            assert "phase" in session

    def test_list_sessions_includes_owner(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should include owner (can be null)."""
        response = app_with_sessions.get(f"/api/v1/projects/{project_id}/sessions")
        data = response.json()

        session_owners = {s["sessionId"]: s.get("owner") for s in data["items"]}
        assert session_owners["session-active-1"] == "leeroy"
        assert session_owners["session-completed-1"] == "jenkins"
        # draft session has no owner
        assert session_owners["session-draft-1"] is None

    def test_list_sessions_includes_task_count(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should include taskCount for each session."""
        response = app_with_sessions.get(f"/api/v1/projects/{project_id}/sessions")
        data = response.json()

        task_counts = {s["sessionId"]: s["taskCount"] for s in data["items"]}
        assert task_counts["session-active-1"] == 3
        assert task_counts["session-completed-1"] == 2
        assert task_counts["session-draft-1"] == 0

    def test_list_sessions_includes_created_at(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should include createdAt for each session."""
        response = app_with_sessions.get(f"/api/v1/projects/{project_id}/sessions")
        data = response.json()

        for session in data["items"]:
            assert "createdAt" in session
            assert session["createdAt"]  # Not empty

    def test_list_sessions_includes_last_active_at(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should include lastActiveAt for each session."""
        response = app_with_sessions.get(f"/api/v1/projects/{project_id}/sessions")
        data = response.json()

        for session in data["items"]:
            assert "lastActiveAt" in session

    def test_list_sessions_includes_git_info(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should include git info (branchName, baseBranch)."""
        response = app_with_sessions.get(f"/api/v1/projects/{project_id}/sessions")
        data = response.json()

        for session in data["items"]:
            assert "git" in session
            git_info = session["git"]
            assert "baseBranch" in git_info

        # Check specific values
        active_session = next(s for s in data["items"] if s["sessionId"] == "session-active-1")
        assert active_session["git"]["branchName"] == "feature/foo"
        assert active_session["git"]["baseBranch"] == "main"

    def test_list_sessions_includes_pagination_info(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should include pagination info (total, limit, offset)."""
        response = app_with_sessions.get(f"/api/v1/projects/{project_id}/sessions")
        data = response.json()

        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert data["total"] == 3

    def test_list_sessions_filter_by_state(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should filter sessions by state."""
        response = app_with_sessions.get(
            f"/api/v1/projects/{project_id}/sessions?state=active"
        )
        data = response.json()

        assert len(data["items"]) == 1
        assert data["items"][0]["sessionId"] == "session-active-1"
        assert data["items"][0]["state"] == "active"

    def test_list_sessions_pagination_limit(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should respect limit parameter."""
        response = app_with_sessions.get(
            f"/api/v1/projects/{project_id}/sessions?limit=2"
        )
        data = response.json()

        assert len(data["items"]) <= 2
        assert data["limit"] == 2

    def test_list_sessions_pagination_offset(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should respect offset parameter."""
        response = app_with_sessions.get(
            f"/api/v1/projects/{project_id}/sessions?offset=1"
        )
        data = response.json()

        assert data["offset"] == 1

    def test_list_sessions_returns_404_for_unknown_project(
        self, app_with_sessions: TestClient
    ) -> None:
        """Should return 404 for unknown project."""
        response = app_with_sessions.get(
            "/api/v1/projects/unknown-project-id/sessions"
        )
        assert response.status_code == 404


class TestSessionReaderService:
    """Tests for the session reader service."""

    def test_reads_all_sessions(self, mock_edison_project_with_sessions: Path) -> None:
        """Should read all sessions from all state directories."""
        from services.session_reader import SessionReaderService

        service = SessionReaderService(str(mock_edison_project_with_sessions))
        sessions = service.list_sessions()

        assert len(sessions) == 3

    def test_parses_session_json_correctly(
        self, mock_edison_project_with_sessions: Path
    ) -> None:
        """Should correctly parse session.json files."""
        from services.session_reader import SessionReaderService

        service = SessionReaderService(str(mock_edison_project_with_sessions))
        sessions = service.list_sessions()

        active_session = next(s for s in sessions if s.session_id == "session-active-1")
        assert active_session.state == "active"
        assert active_session.phase == "implementation"
        assert active_session.owner == "leeroy"

    def test_filters_by_state(self, mock_edison_project_with_sessions: Path) -> None:
        """Should filter sessions by state."""
        from services.session_reader import SessionReaderService

        service = SessionReaderService(str(mock_edison_project_with_sessions))
        sessions = service.list_sessions(state="active")

        assert len(sessions) == 1
        assert sessions[0].session_id == "session-active-1"

    def test_calculates_task_count(
        self, mock_edison_project_with_sessions: Path
    ) -> None:
        """Should calculate task count from tasks index."""
        from services.session_reader import SessionReaderService

        service = SessionReaderService(str(mock_edison_project_with_sessions))
        sessions = service.list_sessions()

        active_session = next(s for s in sessions if s.session_id == "session-active-1")
        assert active_session.task_count == 3

    def test_handles_empty_sessions_dir(self, tmp_path: Path) -> None:
        """Should handle project with no sessions gracefully."""
        from services.session_reader import SessionReaderService

        # Create minimal Edison project without sessions
        project = tmp_path / "empty-project"
        project.mkdir()
        (project / ".edison").mkdir()
        (project / ".project").mkdir()

        service = SessionReaderService(str(project))
        sessions = service.list_sessions()

        assert sessions == []

    def test_handles_missing_project_dir(self, tmp_path: Path) -> None:
        """Should handle missing .project directory gracefully."""
        from services.session_reader import SessionReaderService

        project = tmp_path / "no-project-dir"
        project.mkdir()
        (project / ".edison").mkdir()

        service = SessionReaderService(str(project))
        sessions = service.list_sessions()

        assert sessions == []


class TestSessionSchemas:
    """Tests for session-related Pydantic schemas."""

    def test_session_git_info_schema(self) -> None:
        """Should validate SessionGitInfo schema."""
        from api.schemas.sessions import SessionGitInfo

        git_info = SessionGitInfo(
            branch_name="feature/foo",
            base_branch="main"
        )

        assert git_info.branch_name == "feature/foo"
        assert git_info.base_branch == "main"

    def test_session_git_info_optional_branch_name(self) -> None:
        """Should allow optional branchName."""
        from api.schemas.sessions import SessionGitInfo

        git_info = SessionGitInfo(
            base_branch="main"
        )

        assert git_info.branch_name is None
        assert git_info.base_branch == "main"

    def test_session_list_item_schema(self) -> None:
        """Should validate SessionListItem schema."""
        from api.schemas.sessions import SessionListItem, SessionGitInfo

        session = SessionListItem(
            session_id="test-session",
            state="active",
            phase="implementation",
            owner="leeroy",
            task_count=5,
            created_at="2025-12-27T10:00:00Z",
            last_active_at="2025-12-27T12:00:00Z",
            git=SessionGitInfo(
                branch_name="feature/test",
                base_branch="main"
            )
        )

        assert session.session_id == "test-session"
        assert session.state == "active"
        assert session.task_count == 5

    def test_session_list_item_camel_case_serialization(self) -> None:
        """Should serialize to camelCase for API response."""
        from api.schemas.sessions import SessionListItem, SessionGitInfo

        session = SessionListItem(
            session_id="test-session",
            state="active",
            phase="implementation",
            owner=None,
            task_count=0,
            created_at="2025-12-27T10:00:00Z",
            last_active_at="2025-12-27T12:00:00Z",
            git=SessionGitInfo(base_branch="main")
        )

        data = session.model_dump(by_alias=True)
        assert "sessionId" in data
        assert "taskCount" in data
        assert "createdAt" in data
        assert "lastActiveAt" in data
        assert "branchName" in data["git"]
        assert "baseBranch" in data["git"]

    def test_session_list_response_schema(self) -> None:
        """Should validate SessionListResponse schema."""
        from api.schemas.sessions import SessionListResponse

        response = SessionListResponse(
            items=[],
            total=0,
            limit=100,
            offset=0
        )

        assert response.total == 0
        assert response.limit == 100
