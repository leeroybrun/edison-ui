"""Tests for session context and next endpoints (T070).

RED Phase: These tests MUST fail initially as the endpoints/services don't exist yet.

The endpoints:
- GET /projects/{projectId}/sessions/{sessionId}/context
- GET /projects/{projectId}/sessions/{sessionId}/next
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from main import create_app


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_edison_project_with_sessions(tmp_path: Path) -> Path:
    """Create a mock Edison project with sessions for context/next testing."""
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
            "status": "working",
        },
        "git": {"branchName": "feature/foo", "baseBranch": "main"},
        "tasks": {"T001": "wip", "T002": "todo", "T003": "done"},
    }
    (active_session_dir / "session.json").write_text(json.dumps(active_session_json))

    # Create tasks directory
    tasks_dir = project_dir / "tasks"
    tasks_dir.mkdir()
    for state in ["todo", "wip", "done", "validated"]:
        (tasks_dir / state).mkdir()

    # Create .git directory (marks it as a git repo)
    git_dir = project_path / ".git"
    git_dir.mkdir()

    return project_path


@pytest.fixture
def app_with_sessions(
    mock_edison_project_with_sessions: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    """Create app with mocked scan roots for sessions tests."""
    scan_root = mock_edison_project_with_sessions.parent
    monkeypatch.setenv("SCAN_ROOTS", str(scan_root))
    monkeypatch.setenv("PIN_STORAGE_PATH", str(tmp_path / "pins.json"))

    # Create settings file with localhost mode (no auth required)
    settings_file = tmp_path / "settings.json"
    settings_file.write_text('{"exposureMode": "localhost", "firstRunComplete": true}')
    monkeypatch.setenv("SETTINGS_FILE", str(settings_file))

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


# =============================================================================
# Session Context Endpoint Tests
# =============================================================================


class TestSessionContextEndpoint:
    """Tests for GET /projects/{projectId}/sessions/{sessionId}/context endpoint."""

    def test_context_returns_200_for_valid_session(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return 200 OK for a valid session."""
        with patch("services.session_context.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "isEdisonProject": True,
                    "projectRoot": "/path/to/project",
                    "sessionId": "session-active-1",
                    "sessionState": "active",
                    "worktreePath": "/path/to/worktree",
                    "currentTaskId": "T001",
                    "currentTaskState": "wip",
                    "activePacks": ["python", "typescript"],
                    "constitutions": {
                        "agents": ".edison/_generated/constitutions/AGENTS.md",
                        "orchestrator": ".edison/_generated/constitutions/ORCHESTRATOR.md",
                        "validators": ".edison/_generated/constitutions/VALIDATORS.md",
                    },
                }),
                stderr="",
            )
            response = app_with_sessions.get(
                f"/api/v1/projects/{project_id}/sessions/session-active-1/context"
            )
            assert response.status_code == 200

    def test_context_returns_session_id(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return sessionId in response."""
        with patch("services.session_context.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "isEdisonProject": True,
                    "projectRoot": "/path/to/project",
                    "sessionId": "session-active-1",
                    "sessionState": "active",
                    "worktreePath": None,
                    "currentTaskId": None,
                    "currentTaskState": None,
                    "activePacks": [],
                    "constitutions": {},
                }),
                stderr="",
            )
            response = app_with_sessions.get(
                f"/api/v1/projects/{project_id}/sessions/session-active-1/context"
            )
            data = response.json()
            assert "sessionId" in data
            assert data["sessionId"] == "session-active-1"

    def test_context_returns_session_state(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return sessionState in response."""
        with patch("services.session_context.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "isEdisonProject": True,
                    "projectRoot": "/path/to/project",
                    "sessionId": "session-active-1",
                    "sessionState": "active",
                    "worktreePath": None,
                    "currentTaskId": None,
                    "currentTaskState": None,
                    "activePacks": [],
                    "constitutions": {},
                }),
                stderr="",
            )
            response = app_with_sessions.get(
                f"/api/v1/projects/{project_id}/sessions/session-active-1/context"
            )
            data = response.json()
            assert "sessionState" in data
            assert data["sessionState"] == "active"

    def test_context_returns_is_edison_project(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return isEdisonProject flag."""
        with patch("services.session_context.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "isEdisonProject": True,
                    "projectRoot": "/path/to/project",
                    "sessionId": "session-active-1",
                    "sessionState": "active",
                    "worktreePath": None,
                    "currentTaskId": None,
                    "currentTaskState": None,
                    "activePacks": [],
                    "constitutions": {},
                }),
                stderr="",
            )
            response = app_with_sessions.get(
                f"/api/v1/projects/{project_id}/sessions/session-active-1/context"
            )
            data = response.json()
            assert "isEdisonProject" in data
            assert data["isEdisonProject"] is True

    def test_context_returns_redacted_project_root(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return projectRoot (redacted)."""
        with patch("services.session_context.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "isEdisonProject": True,
                    "projectRoot": "/home/user/secret/project",
                    "sessionId": "session-active-1",
                    "sessionState": "active",
                    "worktreePath": None,
                    "currentTaskId": None,
                    "currentTaskState": None,
                    "activePacks": [],
                    "constitutions": {},
                }),
                stderr="",
            )
            response = app_with_sessions.get(
                f"/api/v1/projects/{project_id}/sessions/session-active-1/context"
            )
            data = response.json()
            assert "projectRoot" in data
            # Path should be redacted
            assert data["projectRoot"] == "[REDACTED]"

    def test_context_returns_redacted_worktree_path(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return worktreePath (redacted)."""
        with patch("services.session_context.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "isEdisonProject": True,
                    "projectRoot": "/home/user/project",
                    "sessionId": "session-active-1",
                    "sessionState": "active",
                    "worktreePath": "/home/user/.worktrees/session-1",
                    "currentTaskId": None,
                    "currentTaskState": None,
                    "activePacks": [],
                    "constitutions": {},
                }),
                stderr="",
            )
            response = app_with_sessions.get(
                f"/api/v1/projects/{project_id}/sessions/session-active-1/context"
            )
            data = response.json()
            assert "worktreePath" in data
            # Path should be redacted
            assert data["worktreePath"] == "[REDACTED]"

    def test_context_returns_null_worktree_path_when_null(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return null worktreePath when no worktree."""
        with patch("services.session_context.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "isEdisonProject": True,
                    "projectRoot": "/home/user/project",
                    "sessionId": "session-active-1",
                    "sessionState": "active",
                    "worktreePath": None,
                    "currentTaskId": None,
                    "currentTaskState": None,
                    "activePacks": [],
                    "constitutions": {},
                }),
                stderr="",
            )
            response = app_with_sessions.get(
                f"/api/v1/projects/{project_id}/sessions/session-active-1/context"
            )
            data = response.json()
            assert data["worktreePath"] is None

    def test_context_returns_current_task_info(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return currentTaskId and currentTaskState."""
        with patch("services.session_context.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "isEdisonProject": True,
                    "projectRoot": "/path/to/project",
                    "sessionId": "session-active-1",
                    "sessionState": "active",
                    "worktreePath": None,
                    "currentTaskId": "T001",
                    "currentTaskState": "wip",
                    "activePacks": [],
                    "constitutions": {},
                }),
                stderr="",
            )
            response = app_with_sessions.get(
                f"/api/v1/projects/{project_id}/sessions/session-active-1/context"
            )
            data = response.json()
            assert data["currentTaskId"] == "T001"
            assert data["currentTaskState"] == "wip"

    def test_context_returns_active_packs(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return activePacks array."""
        with patch("services.session_context.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "isEdisonProject": True,
                    "projectRoot": "/path/to/project",
                    "sessionId": "session-active-1",
                    "sessionState": "active",
                    "worktreePath": None,
                    "currentTaskId": None,
                    "currentTaskState": None,
                    "activePacks": ["python", "typescript"],
                    "constitutions": {},
                }),
                stderr="",
            )
            response = app_with_sessions.get(
                f"/api/v1/projects/{project_id}/sessions/session-active-1/context"
            )
            data = response.json()
            assert "activePacks" in data
            assert data["activePacks"] == ["python", "typescript"]

    def test_context_returns_constitutions(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return constitutions object."""
        with patch("services.session_context.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "isEdisonProject": True,
                    "projectRoot": "/path/to/project",
                    "sessionId": "session-active-1",
                    "sessionState": "active",
                    "worktreePath": None,
                    "currentTaskId": None,
                    "currentTaskState": None,
                    "activePacks": [],
                    "constitutions": {
                        "agents": ".edison/_generated/constitutions/AGENTS.md",
                        "orchestrator": ".edison/_generated/constitutions/ORCHESTRATOR.md",
                        "validators": ".edison/_generated/constitutions/VALIDATORS.md",
                    },
                }),
                stderr="",
            )
            response = app_with_sessions.get(
                f"/api/v1/projects/{project_id}/sessions/session-active-1/context"
            )
            data = response.json()
            assert "constitutions" in data
            assert "agents" in data["constitutions"]
            assert "orchestrator" in data["constitutions"]
            assert "validators" in data["constitutions"]

    def test_context_returns_404_for_unknown_project(
        self, app_with_sessions: TestClient
    ) -> None:
        """Should return 404 for unknown project."""
        response = app_with_sessions.get(
            "/api/v1/projects/unknown-project-id/sessions/session-active-1/context"
        )
        assert response.status_code == 404

    def test_context_returns_error_when_cli_unavailable(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return error response when Edison CLI is unavailable."""
        with patch("services.session_context.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("edison command not found")
            response = app_with_sessions.get(
                f"/api/v1/projects/{project_id}/sessions/session-active-1/context"
            )
            assert response.status_code == 503
            data = response.json()
            assert "error" in data or "detail" in data

    def test_context_returns_error_when_cli_fails(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return error response when Edison CLI returns non-zero."""
        with patch("services.session_context.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Session not found",
            )
            response = app_with_sessions.get(
                f"/api/v1/projects/{project_id}/sessions/session-active-1/context"
            )
            # All CLI errors return 503 (service unavailable)
            assert response.status_code == 503
            data = response.json()
            assert "error" in data or "detail" in data


# =============================================================================
# Session Next Endpoint Tests
# =============================================================================


class TestSessionNextEndpoint:
    """Tests for GET /projects/{projectId}/sessions/{sessionId}/next endpoint."""

    def test_next_returns_200_for_valid_session(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return 200 OK for a valid session."""
        with patch("services.session_next.subprocess.run") as mock_run:
            # Use actual CLI response format: actions array + recommendations array
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "sessionId": "session-active-1",
                    "summary": "Next actions computed",
                    "recommendations": ["## Next Steps", "Claim task T002."],
                    "actions": [
                        {
                            "id": "task.claim",
                            "entity": "task",
                            "recordId": "T002",
                            "rationale": "Task is ready and unassigned",
                        }
                    ],
                    "timestamp": "2025-12-27T10:00:00Z",
                }),
                stderr="",
            )
            response = app_with_sessions.get(
                f"/api/v1/projects/{project_id}/sessions/session-active-1/next"
            )
            assert response.status_code == 200

    def test_next_returns_session_id(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return sessionId in response."""
        with patch("services.session_next.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "sessionId": "session-active-1",
                    "summary": "Some recommendation",
                    "recommendations": [],
                    "actions": [],
                    "timestamp": "2025-12-27T10:00:00Z",
                }),
                stderr="",
            )
            response = app_with_sessions.get(
                f"/api/v1/projects/{project_id}/sessions/session-active-1/next"
            )
            data = response.json()
            assert "sessionId" in data
            assert data["sessionId"] == "session-active-1"

    def test_next_returns_recommendation(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return recommendation markdown string."""
        with patch("services.session_next.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "sessionId": "session-active-1",
                    "recommendations": ["## Next Steps", "Claim task T002."],
                    "actions": [],
                    "timestamp": "2025-12-27T10:00:00Z",
                }),
                stderr="",
            )
            response = app_with_sessions.get(
                f"/api/v1/projects/{project_id}/sessions/session-active-1/next"
            )
            data = response.json()
            assert "recommendation" in data
            assert "Next Steps" in data["recommendation"]

    def test_next_returns_suggested_actions(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return suggestedActions array."""
        with patch("services.session_next.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "sessionId": "session-active-1",
                    "summary": "Claim a task.",
                    "recommendations": [],
                    "actions": [
                        {
                            "id": "task.claim",
                            "entity": "task",
                            "recordId": "T002",
                            "rationale": "Task is ready and unassigned",
                        }
                    ],
                    "timestamp": "2025-12-27T10:00:00Z",
                }),
                stderr="",
            )
            response = app_with_sessions.get(
                f"/api/v1/projects/{project_id}/sessions/session-active-1/next"
            )
            data = response.json()
            assert "suggestedActions" in data
            assert len(data["suggestedActions"]) == 1
            assert data["suggestedActions"][0]["actionType"] == "task.claim"
            assert data["suggestedActions"][0]["taskId"] == "T002"
            assert "reason" in data["suggestedActions"][0]

    def test_next_returns_timestamp(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return timestamp."""
        with patch("services.session_next.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "sessionId": "session-active-1",
                    "summary": "Some recommendation",
                    "recommendations": [],
                    "actions": [],
                    "timestamp": "2025-12-27T10:00:00Z",
                }),
                stderr="",
            )
            response = app_with_sessions.get(
                f"/api/v1/projects/{project_id}/sessions/session-active-1/next"
            )
            data = response.json()
            assert "timestamp" in data
            assert data["timestamp"] == "2025-12-27T10:00:00Z"

    def test_next_returns_404_for_unknown_project(
        self, app_with_sessions: TestClient
    ) -> None:
        """Should return 404 for unknown project."""
        response = app_with_sessions.get(
            "/api/v1/projects/unknown-project-id/sessions/session-active-1/next"
        )
        assert response.status_code == 404

    def test_next_returns_error_when_cli_unavailable(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return error response when Edison CLI is unavailable."""
        with patch("services.session_next.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("edison command not found")
            response = app_with_sessions.get(
                f"/api/v1/projects/{project_id}/sessions/session-active-1/next"
            )
            assert response.status_code == 503
            data = response.json()
            assert "error" in data or "detail" in data

    def test_next_returns_error_when_cli_fails(
        self, app_with_sessions: TestClient, project_id: str
    ) -> None:
        """Should return error response when Edison CLI returns non-zero."""
        with patch("services.session_next.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Session not found",
            )
            response = app_with_sessions.get(
                f"/api/v1/projects/{project_id}/sessions/session-active-1/next"
            )
            # All CLI errors return 503 (service unavailable)
            assert response.status_code == 503
            data = response.json()
            assert "error" in data or "detail" in data


# =============================================================================
# Session Context Service Tests
# =============================================================================


class TestSessionContextService:
    """Tests for SessionContextService."""

    def test_get_context_parses_cli_output(
        self, mock_edison_project_with_sessions: Path
    ) -> None:
        """Should parse JSON output from Edison CLI."""
        from services.session_context import SessionContextService

        service = SessionContextService(str(mock_edison_project_with_sessions))

        with patch("services.session_context.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "isEdisonProject": True,
                    "projectRoot": "/path/to/project",
                    "sessionId": "session-1",
                    "sessionState": "active",
                    "worktreePath": None,
                    "currentTaskId": None,
                    "currentTaskState": None,
                    "activePacks": ["python"],
                    "constitutions": {},
                }),
                stderr="",
            )
            result = service.get_context("session-1")

            assert result.session_id == "session-1"
            assert result.session_state == "active"
            assert result.is_edison_project is True

    def test_get_context_redacts_paths(
        self, mock_edison_project_with_sessions: Path
    ) -> None:
        """Should redact sensitive paths."""
        from services.session_context import SessionContextService

        service = SessionContextService(str(mock_edison_project_with_sessions))

        with patch("services.session_context.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "isEdisonProject": True,
                    "projectRoot": "/home/user/secret/project",
                    "sessionId": "session-1",
                    "sessionState": "active",
                    "worktreePath": "/home/user/.worktrees/session-1",
                    "currentTaskId": None,
                    "currentTaskState": None,
                    "activePacks": [],
                    "constitutions": {},
                }),
                stderr="",
            )
            result = service.get_context("session-1")

            assert result.project_root == "[REDACTED]"
            assert result.worktree_path == "[REDACTED]"

    def test_get_context_raises_on_cli_unavailable(
        self, mock_edison_project_with_sessions: Path
    ) -> None:
        """Should raise error when Edison CLI is unavailable."""
        from services.session_context import SessionContextService, EdisonCLIError

        service = SessionContextService(str(mock_edison_project_with_sessions))

        with patch("services.session_context.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("edison command not found")

            with pytest.raises(EdisonCLIError) as exc_info:
                service.get_context("session-1")

            assert "unavailable" in str(exc_info.value).lower()

    def test_get_context_raises_on_cli_failure(
        self, mock_edison_project_with_sessions: Path
    ) -> None:
        """Should raise error when CLI returns non-zero exit code."""
        from services.session_context import SessionContextService, EdisonCLIError

        service = SessionContextService(str(mock_edison_project_with_sessions))

        with patch("services.session_context.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Session not found",
            )

            with pytest.raises(EdisonCLIError) as exc_info:
                service.get_context("session-1")

            assert "failed" in str(exc_info.value).lower()


# =============================================================================
# Session Next Service Tests
# =============================================================================


class TestSessionNextService:
    """Tests for SessionNextService."""

    def test_get_next_parses_cli_output(
        self, mock_edison_project_with_sessions: Path
    ) -> None:
        """Should parse JSON output from Edison CLI."""
        from services.session_next import SessionNextService

        service = SessionNextService(str(mock_edison_project_with_sessions))

        with patch("services.session_next.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "sessionId": "session-1",
                    "recommendations": ["## Next Steps", "Claim task T002."],
                    "actions": [
                        {
                            "id": "task.claim",
                            "entity": "task",
                            "recordId": "T002",
                            "rationale": "Task is ready",
                        }
                    ],
                    "timestamp": "2025-12-27T10:00:00Z",
                }),
                stderr="",
            )
            result = service.get_next("session-1")

            assert result.session_id == "session-1"
            assert "Next Steps" in result.recommendation
            assert len(result.suggested_actions) == 1

    def test_get_next_parses_suggested_actions(
        self, mock_edison_project_with_sessions: Path
    ) -> None:
        """Should correctly parse suggested actions."""
        from services.session_next import SessionNextService

        service = SessionNextService(str(mock_edison_project_with_sessions))

        with patch("services.session_next.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "sessionId": "session-1",
                    "summary": "Some recommendation",
                    "recommendations": [],
                    "actions": [
                        {
                            "id": "task.claim",
                            "entity": "task",
                            "recordId": "T002",
                            "rationale": "Task is ready",
                        },
                        {
                            "id": "task.complete",
                            "entity": "task",
                            "recordId": "T001",
                            "rationale": "Task is done",
                        },
                    ],
                    "timestamp": "2025-12-27T10:00:00Z",
                }),
                stderr="",
            )
            result = service.get_next("session-1")

            assert len(result.suggested_actions) == 2
            assert result.suggested_actions[0].action_type == "task.claim"
            assert result.suggested_actions[0].task_id == "T002"
            assert result.suggested_actions[1].action_type == "task.complete"

    def test_get_next_raises_on_cli_unavailable(
        self, mock_edison_project_with_sessions: Path
    ) -> None:
        """Should raise error when Edison CLI is unavailable."""
        from services.session_next import SessionNextService, EdisonCLIError

        service = SessionNextService(str(mock_edison_project_with_sessions))

        with patch("services.session_next.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("edison command not found")

            with pytest.raises(EdisonCLIError) as exc_info:
                service.get_next("session-1")

            assert "unavailable" in str(exc_info.value).lower()

    def test_get_next_raises_on_cli_failure(
        self, mock_edison_project_with_sessions: Path
    ) -> None:
        """Should raise error when CLI returns non-zero exit code."""
        from services.session_next import SessionNextService, EdisonCLIError

        service = SessionNextService(str(mock_edison_project_with_sessions))

        with patch("services.session_next.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Session not found",
            )

            with pytest.raises(EdisonCLIError) as exc_info:
                service.get_next("session-1")

            assert "failed" in str(exc_info.value).lower()


# =============================================================================
# Pydantic Schema Tests
# =============================================================================


class TestSessionContextSchemas:
    """Tests for session context Pydantic schemas."""

    def test_session_context_response_schema(self) -> None:
        """Should validate SessionContextResponse schema."""
        from api.schemas.sessions import SessionContextResponse

        response = SessionContextResponse(
            is_edison_project=True,
            project_root="[REDACTED]",
            session_id="session-1",
            session_state="active",
            worktree_path=None,
            current_task_id=None,
            current_task_state=None,
            active_packs=["python"],
            constitutions={"agents": ".edison/_generated/constitutions/AGENTS.md"},
        )

        assert response.session_id == "session-1"
        assert response.is_edison_project is True

    def test_session_context_response_camel_case(self) -> None:
        """Should serialize to camelCase."""
        from api.schemas.sessions import SessionContextResponse

        response = SessionContextResponse(
            is_edison_project=True,
            project_root="[REDACTED]",
            session_id="session-1",
            session_state="active",
            worktree_path=None,
            current_task_id="T001",
            current_task_state="wip",
            active_packs=[],
            constitutions={},
        )

        data = response.model_dump(by_alias=True)
        assert "isEdisonProject" in data
        assert "projectRoot" in data
        assert "sessionId" in data
        assert "sessionState" in data
        assert "worktreePath" in data
        assert "currentTaskId" in data
        assert "currentTaskState" in data
        assert "activePacks" in data


class TestSessionNextSchemas:
    """Tests for session next Pydantic schemas."""

    def test_suggested_action_schema(self) -> None:
        """Should validate SuggestedAction schema."""
        from api.schemas.sessions import SuggestedAction

        action = SuggestedAction(
            action_type="claim-task",
            task_id="T001",
            reason="Task is ready",
        )

        assert action.action_type == "claim-task"
        assert action.task_id == "T001"

    def test_suggested_action_camel_case(self) -> None:
        """Should serialize to camelCase."""
        from api.schemas.sessions import SuggestedAction

        action = SuggestedAction(
            action_type="claim-task",
            task_id="T001",
            reason="Task is ready",
        )

        data = action.model_dump(by_alias=True)
        assert "taskId" in data
        assert "actionType" in data

    def test_session_next_response_schema(self) -> None:
        """Should validate SessionNextResponse schema."""
        from api.schemas.sessions import SessionNextResponse, SuggestedAction

        response = SessionNextResponse(
            session_id="session-1",
            recommendation="## Next Steps\n\nClaim task T002.",
            suggested_actions=[
                SuggestedAction(
                    action_type="claim-task",
                    task_id="T002",
                    reason="Task is ready",
                )
            ],
            timestamp="2025-12-27T10:00:00Z",
        )

        assert response.session_id == "session-1"
        assert len(response.suggested_actions) == 1

    def test_session_next_response_camel_case(self) -> None:
        """Should serialize to camelCase."""
        from api.schemas.sessions import SessionNextResponse

        response = SessionNextResponse(
            session_id="session-1",
            recommendation="Some recommendation",
            suggested_actions=[],
            timestamp="2025-12-27T10:00:00Z",
        )

        data = response.model_dump(by_alias=True)
        assert "sessionId" in data
        assert "suggestedActions" in data
