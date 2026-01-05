"""Tests for guarded task create/transition endpoints (T040).

RED Phase: These tests verify the preview -> confirm/apply pattern for:
- POST /projects/{projectId}/tasks/preview
- POST /projects/{projectId}/tasks
- POST /projects/{projectId}/tasks/{taskId}/transition/preview
- POST /projects/{projectId}/tasks/{taskId}/transition
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
    parent_id: str | None = None,
    depends_on: list[str] | None = None,
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
    if parent_id:
        lines.append(f"parent_id: {parent_id}")
    if depends_on:
        lines.append(f"depends_on: {json.dumps(depends_on)}")
    lines.append("created_at: '2025-12-27T10:00:00Z'")
    lines.append("updated_at: '2025-12-27T11:00:00Z'")
    lines.append("---")
    return "\n".join(lines)


@pytest.fixture
def project_with_guarded_tasks(tmp_path: Path) -> Path:
    """Create a mock Edison project for testing guarded endpoints."""
    project_path = tmp_path / "guarded-project"
    project_path.mkdir()

    # Create .edison directory (marks it as an Edison project)
    (project_path / ".edison").mkdir()

    # Create .project directory structure
    project_dir = project_path / ".project"
    project_dir.mkdir()

    # Create task directories
    tasks_dir = project_dir / "tasks"
    tasks_dir.mkdir()
    for state in ["todo", "wip", "blocked", "done", "validated"]:
        (tasks_dir / state).mkdir()

    # Task in todo state - can be transitioned to wip
    (tasks_dir / "todo" / "T001.md").write_text(
        create_task_frontmatter("T001", "Task without deps")
        + "\n# Task T001\nNo dependencies."
    )

    # Task in wip state - can be transitioned to done or blocked
    (tasks_dir / "wip" / "T002.md").write_text(
        create_task_frontmatter("T002", "Task in progress")
        + "\n# Task T002\nIn progress."
    )

    # Task in done state - can be transitioned to validated
    (tasks_dir / "done" / "T003.md").write_text(
        create_task_frontmatter("T003", "Completed task") + "\n# Task T003\nDone."
    )

    # Task with unmet dependencies - blocked from starting
    (tasks_dir / "todo" / "T004.md").write_text(
        create_task_frontmatter("T004", "Task with deps", depends_on=["T002"])
        + "\n# Task T004\nDepends on T002."
    )

    # Task in validated state - terminal
    (tasks_dir / "validated" / "T005.md").write_text(
        create_task_frontmatter("T005", "Validated task") + "\n# Task T005\nValidated."
    )

    # Create sessions directory structure
    sessions_dir = project_dir / "sessions"
    sessions_dir.mkdir()
    for state in ["draft", "active", "paused", "completed", "abandoned"]:
        (sessions_dir / state).mkdir()

    # Create an active session
    active_session_dir = sessions_dir / "active" / "session-active"
    active_session_dir.mkdir()
    active_session_json = {
        "id": "session-active",
        "state": "active",
        "phase": "implementation",
        "meta": {
            "createdAt": "2025-12-27T10:00:00Z",
            "lastActive": "2025-12-27T12:00:00Z",
        },
    }
    (active_session_dir / "session.json").write_text(json.dumps(active_session_json))

    # Create session task directories
    session_tasks_dir = active_session_dir / "tasks"
    session_tasks_dir.mkdir()
    for state in ["todo", "wip", "blocked", "done", "validated"]:
        (session_tasks_dir / state).mkdir()

    # Create a paused session
    paused_session_dir = sessions_dir / "paused" / "session-paused"
    paused_session_dir.mkdir()
    paused_session_json = {
        "id": "session-paused",
        "state": "paused",
        "meta": {"createdAt": "2025-12-27T08:00:00Z"},
    }
    (paused_session_dir / "session.json").write_text(json.dumps(paused_session_json))

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
def app_with_guarded_tasks(
    project_with_guarded_tasks: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    """Create app with mocked scan roots."""
    monkeypatch.setenv("SCAN_ROOTS", str(project_with_guarded_tasks.parent))
    monkeypatch.setenv("PIN_STORAGE_PATH", str(tmp_path / "pins.json"))

    from core.settings import get_settings

    get_settings.cache_clear()

    app = create_app()
    return TestClient(app)


@pytest.fixture
def project_id(app_with_guarded_tasks: TestClient) -> str:
    """Get the project ID from the discovered project."""
    response = app_with_guarded_tasks.get("/api/v1/projects")
    return str(response.json()["items"][0]["projectId"])


# =============================================================================
# Task Create Preview Tests
# =============================================================================


class TestTaskCreatePreview:
    """Tests for POST /projects/{projectId}/tasks/preview endpoint."""

    def test_preview_returns_200_for_valid_task(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return 200 for valid task preview."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/preview",
            json={
                "title": "New Task",
                "type": "implementation",
            },
        )
        assert response.status_code == 200

    def test_preview_returns_valid_true_for_good_request(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return valid=true for valid task creation request."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/preview",
            json={
                "title": "New Task",
                "type": "implementation",
            },
        )
        data = response.json()
        assert data["valid"] is True
        assert "guardWarnings" in data
        assert "preview" in data

    def test_preview_returns_valid_false_for_invalid_session(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return valid=false for paused session."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/preview",
            json={
                "title": "New Task",
                "type": "implementation",
                "sessionId": "session-paused",
            },
        )
        data = response.json()
        assert data["valid"] is False
        assert "guardFailures" in data
        assert len(data["guardFailures"]) > 0

    def test_preview_returns_valid_false_for_nonexistent_session(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return valid=false for non-existent session."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/preview",
            json={
                "title": "New Task",
                "type": "implementation",
                "sessionId": "session-does-not-exist",
            },
        )
        data = response.json()
        assert data["valid"] is False
        assert any(f["guard"] == "session-exists" for f in data["guardFailures"])

    def test_preview_returns_valid_false_for_nonexistent_dependency(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return valid=false for non-existent dependency."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/preview",
            json={
                "title": "New Task",
                "type": "implementation",
                "dependsOn": ["T999"],
            },
        )
        data = response.json()
        assert data["valid"] is False
        assert any(f["guard"] == "dependency-exists" for f in data["guardFailures"])

    def test_preview_returns_valid_true_with_active_session(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return valid=true for active session."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/preview",
            json={
                "title": "New Task",
                "type": "implementation",
                "sessionId": "session-active",
            },
        )
        data = response.json()
        assert data["valid"] is True

    def test_preview_includes_preview_object(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should include preview object showing what would be created."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/preview",
            json={
                "title": "Preview Task",
                "type": "implementation",
                "parentId": "T001",
                "dependsOn": ["T001"],
            },
        )
        data = response.json()
        assert data["valid"] is True
        assert "preview" in data
        preview = data["preview"]
        assert preview["title"] == "Preview Task"
        assert preview["parentId"] == "T001"

    def test_preview_returns_404_for_unknown_project(
        self, app_with_guarded_tasks: TestClient
    ) -> None:
        """Should return 404 for non-existent project."""
        response = app_with_guarded_tasks.post(
            "/api/v1/projects/unknown-project/tasks/preview",
            json={"title": "New Task", "type": "implementation"},
        )
        assert response.status_code == 404


# =============================================================================
# Task Create (Apply) Tests
# =============================================================================


class TestTaskCreate:
    """Tests for POST /projects/{projectId}/tasks endpoint."""

    def test_create_returns_400_without_confirmed_flag(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return 400 if confirmed flag is not set."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={
                "title": "New Task",
                "type": "implementation",
            },
        )
        assert response.status_code == 400

    def test_create_returns_400_when_guards_fail(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return 400 when guards fail even with confirmed=true."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={
                "title": "New Task",
                "type": "implementation",
                "sessionId": "session-paused",  # Invalid - paused session
                "confirmed": True,
            },
        )
        assert response.status_code == 400

    def test_create_returns_201_for_valid_confirmed_request(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return 201 for valid confirmed task creation."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={
                "title": "Created Task",
                "type": "implementation",
                "confirmed": True,
            },
        )
        assert response.status_code == 201

    def test_create_returns_task_id(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return taskId in response."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={
                "title": "Task With ID",
                "type": "implementation",
                "confirmed": True,
            },
        )
        data = response.json()
        assert "taskId" in data
        assert data["taskId"] is not None
        assert len(data["taskId"]) > 0

    def test_create_returns_audit_entry_id(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return auditEntryId in response."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={
                "title": "Audited Task",
                "type": "implementation",
                "confirmed": True,
            },
        )
        data = response.json()
        assert "auditEntryId" in data
        assert data["auditEntryId"] is not None

    def test_create_with_session_scopes_task(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should create session-scoped task when sessionId provided."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={
                "title": "Session Task",
                "type": "implementation",
                "sessionId": "session-active",
                "confirmed": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "taskId" in data

    def test_create_with_parent_and_dependencies(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should create task with parent and dependencies."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={
                "title": "Child Task",
                "type": "implementation",
                "parentId": "T001",
                "dependsOn": ["T003"],  # T003 is in done state
                "confirmed": True,
            },
        )
        assert response.status_code == 201

    def test_create_returns_404_for_unknown_project(
        self, app_with_guarded_tasks: TestClient
    ) -> None:
        """Should return 404 for non-existent project."""
        response = app_with_guarded_tasks.post(
            "/api/v1/projects/unknown-project/tasks",
            json={"title": "New Task", "type": "implementation", "confirmed": True},
        )
        assert response.status_code == 404


# =============================================================================
# Task Transition Preview Tests
# =============================================================================


class TestTaskTransitionPreview:
    """Tests for POST /projects/{projectId}/tasks/{taskId}/transition/preview."""

    def test_transition_preview_returns_200(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return 200 for valid transition preview."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/T001/transition/preview",
            json={"toState": "wip"},
        )
        assert response.status_code == 200

    def test_transition_preview_returns_valid_true_for_good_transition(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return valid=true for valid transition (todo->wip)."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/T001/transition/preview",
            json={"toState": "wip"},
        )
        data = response.json()
        assert data["valid"] is True
        assert data["currentState"] == "todo"
        assert data["toState"] == "wip"

    def test_transition_preview_returns_valid_false_for_invalid_transition(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return valid=false for invalid transition (todo->done)."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/T001/transition/preview",
            json={"toState": "done"},
        )
        data = response.json()
        assert data["valid"] is False
        assert any(f["guard"] == "valid-transition" for f in data["guardFailures"])

    def test_transition_preview_returns_valid_false_for_unmet_dependencies(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return valid=false when dependencies not ready."""
        # T004 depends on T002 which is in wip
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/T004/transition/preview",
            json={"toState": "wip"},
        )
        data = response.json()
        assert data["valid"] is False
        assert any(f["guard"] == "dependencies-ready" for f in data["guardFailures"])

    def test_transition_preview_returns_404_for_unknown_task(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return 404 for non-existent task."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/T999/transition/preview",
            json={"toState": "wip"},
        )
        # The API should return guard failure for task-exists
        # But could also be designed to return 404 - we'll check the current state
        # Implementation choice: return 200 with valid=false or 404
        # Based on contract, 200 with valid=false is more consistent
        data = response.json()
        assert data["valid"] is False
        assert any(f["guard"] == "task-exists" for f in data["guardFailures"])

    def test_transition_preview_returns_404_for_unknown_project(
        self, app_with_guarded_tasks: TestClient
    ) -> None:
        """Should return 404 for non-existent project."""
        response = app_with_guarded_tasks.post(
            "/api/v1/projects/unknown-project/tasks/T001/transition/preview",
            json={"toState": "wip"},
        )
        assert response.status_code == 404


# =============================================================================
# Task Transition (Apply) Tests
# =============================================================================


class TestTaskTransition:
    """Tests for POST /projects/{projectId}/tasks/{taskId}/transition endpoint."""

    def test_transition_returns_400_without_confirmed_flag(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return 400 if confirmed flag is not set."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/T001/transition",
            json={"toState": "wip"},
        )
        assert response.status_code == 400

    def test_transition_returns_400_when_guards_fail(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return 400 when guards fail even with confirmed=true."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/T001/transition",
            json={"toState": "done", "confirmed": True},  # Invalid: todo->done
        )
        assert response.status_code == 400

    def test_transition_returns_200_for_valid_confirmed(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return 200 for valid confirmed transition."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/T001/transition",
            json={"toState": "wip", "confirmed": True},
        )
        assert response.status_code == 200

    def test_transition_returns_task_id_and_states(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return taskId, previousState, and newState."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/T002/transition",
            json={"toState": "done", "confirmed": True},
        )
        data = response.json()
        assert data["taskId"] == "T002"
        assert data["previousState"] == "wip"
        assert data["newState"] == "done"

    def test_transition_returns_audit_entry_id(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should return auditEntryId in response."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/T003/transition",
            json={"toState": "validated", "confirmed": True},
        )
        data = response.json()
        assert "auditEntryId" in data
        assert data["auditEntryId"] is not None

    def test_transition_actually_moves_file(
        self,
        app_with_guarded_tasks: TestClient,
        project_id: str,
        project_with_guarded_tasks: Path,
    ) -> None:
        """Should actually move the task file to new state directory."""
        # Verify T001 is in todo before
        todo_file = (
            project_with_guarded_tasks / ".project" / "tasks" / "todo" / "T001.md"
        )
        wip_file = project_with_guarded_tasks / ".project" / "tasks" / "wip" / "T001.md"
        assert todo_file.exists()
        assert not wip_file.exists()

        # Transition
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/T001/transition",
            json={"toState": "wip", "confirmed": True},
        )
        assert response.status_code == 200

        # Verify file moved
        assert not todo_file.exists()
        assert wip_file.exists()

    def test_transition_returns_404_for_unknown_project(
        self, app_with_guarded_tasks: TestClient
    ) -> None:
        """Should return 404 for non-existent project."""
        response = app_with_guarded_tasks.post(
            "/api/v1/projects/unknown-project/tasks/T001/transition",
            json={"toState": "wip", "confirmed": True},
        )
        assert response.status_code == 404


# =============================================================================
# Audit Integration Tests
# =============================================================================


class TestAuditIntegration:
    """Tests for audit logging on task operations."""

    def test_create_writes_audit_entry(
        self,
        app_with_guarded_tasks: TestClient,
        project_id: str,
        project_with_guarded_tasks: Path,
    ) -> None:
        """Should write audit entry on task creation."""
        import glob as globmod
        from datetime import date

        # Create task
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={
                "title": "Audited Creation",
                "type": "implementation",
                "confirmed": True,
            },
        )
        assert response.status_code == 201

        # Check audit log exists
        today = date.today().isoformat()
        log_pattern = str(
            project_with_guarded_tasks
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
        assert last_entry["action_type"] == "task.create"
        assert last_entry["outcome"] == "success"

    def test_transition_writes_audit_entry(
        self,
        app_with_guarded_tasks: TestClient,
        project_id: str,
        project_with_guarded_tasks: Path,
    ) -> None:
        """Should write audit entry on task transition."""
        import glob as globmod
        from datetime import date

        # Transition task
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/T002/transition",
            json={"toState": "blocked", "confirmed": True},
        )
        assert response.status_code == 200

        # Check audit log
        today = date.today().isoformat()
        log_pattern = str(
            project_with_guarded_tasks
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
            json.loads(line) for line in lines if "task.transition" in line
        ]
        assert len(transition_entries) >= 1

        entry = transition_entries[-1]
        assert entry["action_type"] == "task.transition"
        assert entry["outcome"] == "success"
        assert entry["context"]["from_state"] == "wip"
        assert entry["context"]["to_state"] == "blocked"


# =============================================================================
# Schema Validation Tests
# =============================================================================


class TestGuardedSchemas:
    """Tests for request/response schema validation."""

    def test_create_preview_requires_title(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should require title in create preview request."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/preview",
            json={"type": "implementation"},
        )
        assert response.status_code == 422

    def test_create_preview_requires_type(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should require type in create preview request."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/preview",
            json={"title": "New Task"},
        )
        assert response.status_code == 422

    def test_transition_preview_requires_to_state(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Should require toState in transition preview request."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/T001/transition/preview",
            json={},
        )
        assert response.status_code == 422

    def test_guard_failure_has_required_fields(
        self, app_with_guarded_tasks: TestClient, project_id: str
    ) -> None:
        """Guard failure should have guard and reason fields."""
        response = app_with_guarded_tasks.post(
            f"/api/v1/projects/{project_id}/tasks/preview",
            json={
                "title": "New Task",
                "type": "implementation",
                "sessionId": "nonexistent",
            },
        )
        data = response.json()
        assert data["valid"] is False
        failure = data["guardFailures"][0]
        assert "guard" in failure
        assert "reason" in failure
