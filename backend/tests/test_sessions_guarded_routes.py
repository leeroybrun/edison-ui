"""Tests for guarded session create/transition endpoints (T041).

RED Phase: These tests verify the preview -> confirm/apply pattern for:
- POST /projects/{projectId}/sessions/create/preview
- POST /projects/{projectId}/sessions
- POST /projects/{projectId}/sessions/{sessionId}/transition/preview
- POST /projects/{projectId}/sessions/{sessionId}/transition
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import create_app


def create_task_frontmatter(
    task_id: str,
    title: str,
    task_type: str = "implementation",
    session_id: str | None = None,
) -> str:
    """Create YAML frontmatter for a task file."""
    lines = [
        "---",
        f"id: {task_id}",
        f"title: {title}",
        f"type: {task_type}",
    ]
    if session_id:
        lines.append(f"session_id: {session_id}")
    lines.append("created_at: '2025-12-27T10:00:00Z'")
    lines.append("updated_at: '2025-12-27T11:00:00Z'")
    lines.append("---")
    return "\n".join(lines)


@pytest.fixture
def project_with_guarded_sessions(tmp_path: Path) -> Path:
    """Create a mock Edison project for testing guarded session endpoints."""
    project_path = tmp_path / "guarded-sessions-project"
    project_path.mkdir()

    # Create .edison directory (marks it as an Edison project)
    (project_path / ".edison").mkdir()

    # Create .project directory structure
    project_dir = project_path / ".project"
    project_dir.mkdir()

    # Create global task directories
    tasks_dir = project_dir / "tasks"
    tasks_dir.mkdir()
    for state in ["todo", "wip", "blocked", "done", "validated"]:
        (tasks_dir / state).mkdir()

    # Create sessions directory structure
    sessions_dir = project_dir / "sessions"
    sessions_dir.mkdir()
    for state in ["draft", "active", "paused", "completed", "abandoned"]:
        (sessions_dir / state).mkdir()

    # Create a draft session WITHOUT tasks (cannot activate)
    draft_no_task_dir = sessions_dir / "draft" / "session-draft-no-task"
    draft_no_task_dir.mkdir()
    draft_no_task_json = {
        "id": "session-draft-no-task",
        "state": "draft",
        "meta": {
            "createdAt": "2025-12-27T10:00:00Z",
            "owner": "test-user",
        },
        "git": {
            "baseBranch": "main",
            "branchName": "session/draft-no-task",
        },
        "tasks": {},
    }
    (draft_no_task_dir / "session.json").write_text(json.dumps(draft_no_task_json))

    # Create task directories for draft-no-task session
    draft_no_task_tasks_dir = draft_no_task_dir / "tasks"
    draft_no_task_tasks_dir.mkdir()
    for state in ["todo", "wip", "blocked", "done", "validated"]:
        (draft_no_task_tasks_dir / state).mkdir()

    # Create a draft session WITH tasks (can activate)
    draft_with_task_dir = sessions_dir / "draft" / "session-draft-with-task"
    draft_with_task_dir.mkdir()
    draft_with_task_json = {
        "id": "session-draft-with-task",
        "state": "draft",
        "meta": {
            "createdAt": "2025-12-27T10:00:00Z",
            "owner": "test-user",
        },
        "git": {
            "baseBranch": "main",
            "branchName": "session/draft-with-task",
        },
        "tasks": {"T100": "todo"},
    }
    (draft_with_task_dir / "session.json").write_text(json.dumps(draft_with_task_json))

    # Create task directories
    draft_with_task_tasks_dir = draft_with_task_dir / "tasks"
    draft_with_task_tasks_dir.mkdir()
    for state in ["todo", "wip", "blocked", "done", "validated"]:
        (draft_with_task_tasks_dir / state).mkdir()

    # Add a task
    (draft_with_task_tasks_dir / "todo" / "T100.md").write_text(
        create_task_frontmatter(
            "T100", "Session task", session_id="session-draft-with-task"
        )
        + "\n# Task T100\nSession scoped task."
    )

    # Create an active session with incomplete tasks
    active_session_dir = sessions_dir / "active" / "session-active"
    active_session_dir.mkdir()
    active_session_json = {
        "id": "session-active",
        "state": "active",
        "phase": "implementation",
        "meta": {
            "createdAt": "2025-12-27T10:00:00Z",
            "lastActive": "2025-12-27T12:00:00Z",
            "owner": "test-user",
        },
        "git": {
            "baseBranch": "main",
            "branchName": "session/active",
        },
        "tasks": {"T101": "wip"},
    }
    (active_session_dir / "session.json").write_text(json.dumps(active_session_json))

    # Create task directories
    active_tasks_dir = active_session_dir / "tasks"
    active_tasks_dir.mkdir()
    for state in ["todo", "wip", "blocked", "done", "validated"]:
        (active_tasks_dir / state).mkdir()

    # Add a task in wip
    (active_tasks_dir / "wip" / "T101.md").write_text(
        create_task_frontmatter(
            "T101", "Active session task", session_id="session-active"
        )
        + "\n# Task T101\nIn progress."
    )

    # Create an active session with all tasks completed
    active_complete_dir = sessions_dir / "active" / "session-active-complete"
    active_complete_dir.mkdir()
    active_complete_json = {
        "id": "session-active-complete",
        "state": "active",
        "phase": "implementation",
        "meta": {
            "createdAt": "2025-12-27T10:00:00Z",
            "lastActive": "2025-12-27T12:00:00Z",
            "owner": "test-user",
        },
        "git": {
            "baseBranch": "main",
            "branchName": "session/active-complete",
        },
        "tasks": {"T102": "done"},
    }
    (active_complete_dir / "session.json").write_text(json.dumps(active_complete_json))

    # Create task directories
    active_complete_tasks_dir = active_complete_dir / "tasks"
    active_complete_tasks_dir.mkdir()
    for state in ["todo", "wip", "blocked", "done", "validated"]:
        (active_complete_tasks_dir / state).mkdir()

    # Add a task in done state
    (active_complete_tasks_dir / "done" / "T102.md").write_text(
        create_task_frontmatter(
            "T102", "Completed task", session_id="session-active-complete"
        )
        + "\n# Task T102\nDone."
    )

    # Create a completed session
    completed_session_dir = sessions_dir / "completed" / "session-completed"
    completed_session_dir.mkdir()
    completed_session_json = {
        "id": "session-completed",
        "state": "completed",
        "meta": {
            "createdAt": "2025-12-27T06:00:00Z",
        },
        "git": {
            "baseBranch": "main",
            "branchName": "session/completed",
        },
        "tasks": {},
    }
    (completed_session_dir / "session.json").write_text(
        json.dumps(completed_session_json)
    )

    # Create logs directory for audit
    logs_dir = project_dir / "logs" / "edison"
    logs_dir.mkdir(parents=True)

    # Create QA directories
    qa_dir = project_dir / "qa"
    qa_dir.mkdir()
    for state in ["waiting", "todo", "wip", "done", "validated"]:
        (qa_dir / state).mkdir()

    # Create .git directory
    (project_path / ".git").mkdir()

    return project_path


@pytest.fixture
def app_with_guarded_sessions(
    project_with_guarded_sessions: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    """Create app with mocked scan roots."""
    monkeypatch.setenv("SCAN_ROOTS", str(project_with_guarded_sessions.parent))
    monkeypatch.setenv("PIN_STORAGE_PATH", str(tmp_path / "pins.json"))

    from core.settings import get_settings

    get_settings.cache_clear()

    app = create_app()
    return TestClient(app)


@pytest.fixture
def project_id(app_with_guarded_sessions: TestClient) -> str:
    """Get the project ID from the discovered project."""
    response = app_with_guarded_sessions.get("/api/v1/projects")
    return str(response.json()["items"][0]["projectId"])


# =============================================================================
# Session Create Preview Tests
# =============================================================================


class TestSessionCreatePreview:
    """Tests for POST /projects/{projectId}/sessions/create/preview endpoint."""

    def test_preview_returns_200_for_valid_session(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should return 200 for valid session preview."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions/create/preview",
            json={
                "owner": "test-user",
                "baseBranch": "main",
            },
        )
        assert response.status_code == 200

    def test_preview_returns_valid_true_for_good_request(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should return valid=true for valid session creation request."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions/create/preview",
            json={
                "owner": "test-user",
                "baseBranch": "main",
            },
        )
        data = response.json()
        assert data["valid"] is True
        assert "guardWarnings" in data
        assert "preview" in data

    def test_preview_returns_valid_true_with_null_owner(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should return valid=true when owner is null."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions/create/preview",
            json={
                "owner": None,
                "baseBranch": "main",
            },
        )
        data = response.json()
        assert data["valid"] is True

    def test_preview_includes_preview_object(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should include preview object showing what would be created."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions/create/preview",
            json={
                "owner": "preview-owner",
                "baseBranch": "develop",
            },
        )
        data = response.json()
        assert data["valid"] is True
        assert "preview" in data
        preview = data["preview"]
        assert preview["owner"] == "preview-owner"
        assert preview["baseBranch"] == "develop"

    def test_preview_returns_404_for_unknown_project(
        self, app_with_guarded_sessions: TestClient
    ) -> None:
        """Should return 404 for non-existent project."""
        response = app_with_guarded_sessions.post(
            "/api/v1/projects/unknown-project/sessions/create/preview",
            json={"owner": "test", "baseBranch": "main"},
        )
        assert response.status_code == 404


# =============================================================================
# Session Create (Apply) Tests
# =============================================================================


class TestSessionCreate:
    """Tests for POST /projects/{projectId}/sessions endpoint."""

    def test_create_returns_400_without_confirmed_flag(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should return 400 if confirmed flag is not set."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions",
            json={
                "owner": "test-user",
                "baseBranch": "main",
            },
        )
        assert response.status_code == 400

    def test_create_returns_201_for_valid_confirmed_request(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should return 201 for valid confirmed session creation."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions",
            json={
                "owner": "test-user",
                "baseBranch": "main",
                "confirmed": True,
            },
        )
        assert response.status_code == 201

    def test_create_returns_session_id(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should return sessionId in response."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions",
            json={
                "owner": "test-user",
                "baseBranch": "main",
                "confirmed": True,
            },
        )
        data = response.json()
        assert "sessionId" in data
        assert data["sessionId"] is not None
        assert len(data["sessionId"]) > 0

    def test_create_returns_audit_entry_id(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should return auditEntryId in response."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions",
            json={
                "owner": "audited-user",
                "baseBranch": "main",
                "confirmed": True,
            },
        )
        data = response.json()
        assert "auditEntryId" in data
        assert data["auditEntryId"] is not None

    def test_create_with_null_owner(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should create session without owner."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions",
            json={
                "owner": None,
                "baseBranch": "main",
                "confirmed": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "sessionId" in data

    def test_create_returns_404_for_unknown_project(
        self, app_with_guarded_sessions: TestClient
    ) -> None:
        """Should return 404 for non-existent project."""
        response = app_with_guarded_sessions.post(
            "/api/v1/projects/unknown-project/sessions",
            json={"owner": "test", "baseBranch": "main", "confirmed": True},
        )
        assert response.status_code == 404


# =============================================================================
# Session Transition Preview Tests
# =============================================================================


class TestSessionTransitionPreview:
    """Tests for POST /projects/{projectId}/sessions/{sessionId}/transition/preview."""

    def test_transition_preview_returns_200(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should return 200 for valid transition preview."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions/session-draft-with-task/transition/preview",
            json={"toState": "active"},
        )
        assert response.status_code == 200

    def test_transition_preview_returns_valid_true_for_good_transition(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should return valid=true for valid transition (draft->active with task)."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions/session-draft-with-task/transition/preview",
            json={"toState": "active"},
        )
        data = response.json()
        assert data["valid"] is True
        assert data["currentState"] == "draft"
        assert data["toState"] == "active"

    def test_transition_preview_returns_valid_false_for_missing_task(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should return valid=false for draft->active without task."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions/session-draft-no-task/transition/preview",
            json={"toState": "active"},
        )
        data = response.json()
        assert data["valid"] is False
        assert any(f["guard"] == "has-task" for f in data["guardFailures"])

    def test_transition_preview_returns_valid_false_for_invalid_transition(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should return valid=false for invalid transition (draft->completed)."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions/session-draft-with-task/transition/preview",
            json={"toState": "completed"},
        )
        data = response.json()
        assert data["valid"] is False
        assert any(f["guard"] == "valid-transition" for f in data["guardFailures"])

    def test_transition_preview_returns_valid_false_for_incomplete_work(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should return valid=false when transitioning to done with incomplete tasks."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions/session-active/transition/preview",
            json={"toState": "done"},
        )
        data = response.json()
        assert data["valid"] is False
        assert any(f["guard"] == "all-work-complete" for f in data["guardFailures"])

    def test_transition_preview_returns_valid_false_for_unknown_session(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should return valid=false for non-existent session."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions/session-does-not-exist/transition/preview",
            json={"toState": "active"},
        )
        data = response.json()
        assert data["valid"] is False
        assert any(f["guard"] == "session-exists" for f in data["guardFailures"])

    def test_transition_preview_returns_404_for_unknown_project(
        self, app_with_guarded_sessions: TestClient
    ) -> None:
        """Should return 404 for non-existent project."""
        response = app_with_guarded_sessions.post(
            "/api/v1/projects/unknown-project/sessions/session-active/transition/preview",
            json={"toState": "done"},
        )
        assert response.status_code == 404


# =============================================================================
# Session Transition (Apply) Tests
# =============================================================================


class TestSessionTransition:
    """Tests for POST /projects/{projectId}/sessions/{sessionId}/transition endpoint."""

    def test_transition_returns_400_without_confirmed_flag(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should return 400 if confirmed flag is not set."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions/session-draft-with-task/transition",
            json={"toState": "active"},
        )
        assert response.status_code == 400

    def test_transition_returns_400_when_guards_fail(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should return 400 when guards fail even with confirmed=true."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions/session-draft-no-task/transition",
            json={"toState": "active", "confirmed": True},
        )
        assert response.status_code == 400

    def test_transition_returns_200_for_valid_confirmed(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should return 200 for valid confirmed transition."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions/session-draft-with-task/transition",
            json={"toState": "active", "confirmed": True},
        )
        assert response.status_code == 200

    def test_transition_returns_session_id_and_states(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should return sessionId, previousState, and newState."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions/session-draft-with-task/transition",
            json={"toState": "active", "confirmed": True},
        )
        data = response.json()
        assert data["sessionId"] == "session-draft-with-task"
        assert data["previousState"] == "draft"
        assert data["newState"] == "active"

    def test_transition_returns_audit_entry_id(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should return auditEntryId in response."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions/session-active/transition",
            json={"toState": "blocked", "confirmed": True},
        )
        data = response.json()
        assert "auditEntryId" in data
        assert data["auditEntryId"] is not None

    def test_transition_actually_moves_session(
        self,
        app_with_guarded_sessions: TestClient,
        project_id: str,
        project_with_guarded_sessions: Path,
    ) -> None:
        """Should actually move the session directory to new state."""
        # Verify session is in draft before
        draft_dir = (
            project_with_guarded_sessions
            / ".project"
            / "sessions"
            / "draft"
            / "session-draft-with-task"
        )
        active_dir = (
            project_with_guarded_sessions
            / ".project"
            / "sessions"
            / "active"
            / "session-draft-with-task"
        )
        assert draft_dir.exists()
        assert not active_dir.exists()

        # Transition
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions/session-draft-with-task/transition",
            json={"toState": "active", "confirmed": True},
        )
        assert response.status_code == 200

        # Verify directory moved
        assert not draft_dir.exists()
        assert active_dir.exists()

    def test_transition_returns_404_for_unknown_project(
        self, app_with_guarded_sessions: TestClient
    ) -> None:
        """Should return 404 for non-existent project."""
        response = app_with_guarded_sessions.post(
            "/api/v1/projects/unknown-project/sessions/session-active/transition",
            json={"toState": "done", "confirmed": True},
        )
        assert response.status_code == 404


# =============================================================================
# Audit Integration Tests
# =============================================================================


class TestAuditIntegration:
    """Tests for audit logging on session operations."""

    def test_create_writes_audit_entry(
        self,
        app_with_guarded_sessions: TestClient,
        project_id: str,
        project_with_guarded_sessions: Path,
    ) -> None:
        """Should write audit entry on session creation."""
        import glob as globmod
        from datetime import date

        # Create session
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions",
            json={
                "owner": "audited-creation",
                "baseBranch": "main",
                "confirmed": True,
            },
        )
        assert response.status_code == 201

        # Check audit log exists
        today = date.today().isoformat()
        log_pattern = str(
            project_with_guarded_sessions
            / ".project"
            / "logs"
            / "edison"
            / f"audit-{today}.jsonl"
        )
        log_files = globmod.glob(log_pattern)
        assert len(log_files) == 1

        # Read and verify audit entry
        with open(log_files[0]) as f:
            lines = f.readlines()
        assert len(lines) >= 1

        last_entry = json.loads(lines[-1])
        assert last_entry["action_type"] == "session.create"
        assert last_entry["outcome"] == "success"

    def test_transition_writes_audit_entry(
        self,
        app_with_guarded_sessions: TestClient,
        project_id: str,
        project_with_guarded_sessions: Path,
    ) -> None:
        """Should write audit entry on session transition."""
        import glob as globmod
        from datetime import date

        # Transition session
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions/session-active/transition",
            json={"toState": "blocked", "confirmed": True},
        )
        assert response.status_code == 200

        # Check audit log
        today = date.today().isoformat()
        log_pattern = str(
            project_with_guarded_sessions
            / ".project"
            / "logs"
            / "edison"
            / f"audit-{today}.jsonl"
        )
        log_files = globmod.glob(log_pattern)
        assert len(log_files) == 1

        with open(log_files[0]) as f:
            lines = f.readlines()

        # Find the transition entry
        transition_entries = [
            json.loads(line) for line in lines if "session.transition" in line
        ]
        assert len(transition_entries) >= 1

        entry = transition_entries[-1]
        assert entry["action_type"] == "session.transition"
        assert entry["outcome"] == "success"
        assert entry["context"]["from_state"] == "active"
        assert entry["context"]["to_state"] == "blocked"


# =============================================================================
# Schema Validation Tests
# =============================================================================


class TestGuardedSchemas:
    """Tests for request/response schema validation."""

    def test_create_preview_requires_base_branch(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should require baseBranch in create preview request."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions/create/preview",
            json={"owner": "test-user"},
        )
        assert response.status_code == 422

    def test_transition_preview_requires_to_state(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Should require toState in transition preview request."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions/session-active/transition/preview",
            json={},
        )
        assert response.status_code == 422

    def test_guard_failure_has_required_fields(
        self, app_with_guarded_sessions: TestClient, project_id: str
    ) -> None:
        """Guard failure should have guard and reason fields."""
        response = app_with_guarded_sessions.post(
            f"/api/v1/projects/{project_id}/sessions/session-does-not-exist/transition/preview",
            json={"toState": "active"},
        )
        data = response.json()
        assert data["valid"] is False
        failure = data["guardFailures"][0]
        assert "guard" in failure
        assert "reason" in failure
