"""Tests for task guard service (T040).

RED Phase: These tests verify task operation guards including:
- Session state validation
- Dependency validation
- State transition validation
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


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
def project_with_guards_setup(tmp_path: Path) -> Path:
    """Create a mock Edison project with various session/task states for guard testing."""
    project_path = tmp_path / "guard-test-project"
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

    # Task in todo - ready to work on
    (tasks_dir / "todo" / "T001.md").write_text(
        create_task_frontmatter("T001", "Task without deps")
        + "\n# Task T001\nNo dependencies."
    )

    # Task in wip
    (tasks_dir / "wip" / "T002.md").write_text(
        create_task_frontmatter("T002", "Task in progress")
        + "\n# Task T002\nIn progress."
    )

    # Task in todo with dependencies on T002 (not done)
    (tasks_dir / "todo" / "T003.md").write_text(
        create_task_frontmatter("T003", "Task with deps", depends_on=["T002"])
        + "\n# Task T003\nDepends on T002."
    )

    # Task in done state
    (tasks_dir / "done" / "T004.md").write_text(
        create_task_frontmatter("T004", "Completed task")
        + "\n# Task T004\nDone."
    )

    # Task in validated state
    (tasks_dir / "validated" / "T005.md").write_text(
        create_task_frontmatter("T005", "Validated task")
        + "\n# Task T005\nValidated."
    )

    # Task depending on validated task (should be able to start)
    (tasks_dir / "todo" / "T006.md").write_text(
        create_task_frontmatter("T006", "Task with done deps", depends_on=["T005"])
        + "\n# Task T006\nDepends on validated T005."
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

    # Create session-scoped task directories
    session_tasks_dir = active_session_dir / "tasks"
    session_tasks_dir.mkdir()
    for state in ["todo", "wip", "blocked", "done", "validated"]:
        (session_tasks_dir / state).mkdir()

    # Session-scoped task
    (session_tasks_dir / "todo" / "T100.md").write_text(
        create_task_frontmatter("T100", "Session task", session_id="session-active")
        + "\n# Task T100\nSession scoped."
    )

    # Create a paused session
    paused_session_dir = sessions_dir / "paused" / "session-paused"
    paused_session_dir.mkdir()
    paused_session_json = {
        "id": "session-paused",
        "state": "paused",
        "phase": "implementation",
        "meta": {
            "createdAt": "2025-12-27T08:00:00Z",
            "lastActive": "2025-12-27T09:00:00Z",
        },
    }
    (paused_session_dir / "session.json").write_text(json.dumps(paused_session_json))

    # Create a completed session
    completed_session_dir = sessions_dir / "completed" / "session-completed"
    completed_session_dir.mkdir()
    completed_session_json = {
        "id": "session-completed",
        "state": "completed",
        "meta": {
            "createdAt": "2025-12-27T06:00:00Z",
        },
    }
    (completed_session_dir / "session.json").write_text(
        json.dumps(completed_session_json)
    )

    # Create .git directory
    (project_path / ".git").mkdir()

    return project_path


# =============================================================================
# TaskGuardService Tests - Session Validation
# =============================================================================


class TestSessionGuards:
    """Tests for session-related guard checks."""

    def test_active_session_allows_task_creation(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should allow task creation in active session."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_create_guards(
            title="New task",
            task_type="implementation",
            session_id="session-active",
        )

        assert result.valid is True
        assert len(result.failures) == 0

    def test_paused_session_blocks_task_creation(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should block task creation in paused session."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_create_guards(
            title="New task",
            task_type="implementation",
            session_id="session-paused",
        )

        assert result.valid is False
        assert any(f.guard == "session-active" for f in result.failures)

    def test_completed_session_blocks_task_creation(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should block task creation in completed session."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_create_guards(
            title="New task",
            task_type="implementation",
            session_id="session-completed",
        )

        assert result.valid is False
        assert any(f.guard == "session-active" for f in result.failures)

    def test_nonexistent_session_blocks_task_creation(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should block task creation for non-existent session."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_create_guards(
            title="New task",
            task_type="implementation",
            session_id="session-does-not-exist",
        )

        assert result.valid is False
        assert any(f.guard == "session-exists" for f in result.failures)

    def test_null_session_allows_global_task_creation(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should allow global (unscoped) task creation without session."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_create_guards(
            title="Global task",
            task_type="implementation",
            session_id=None,
        )

        assert result.valid is True
        assert len(result.failures) == 0


# =============================================================================
# TaskGuardService Tests - Dependency Validation
# =============================================================================


class TestDependencyGuards:
    """Tests for dependency-related guard checks."""

    def test_nonexistent_dependency_fails(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should fail when depending on non-existent task."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_create_guards(
            title="New task",
            task_type="implementation",
            session_id=None,
            depends_on=["T999"],  # Doesn't exist
        )

        assert result.valid is False
        assert any(f.guard == "dependency-exists" for f in result.failures)

    def test_valid_dependencies_pass(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should pass when all dependencies exist."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_create_guards(
            title="New task",
            task_type="implementation",
            session_id=None,
            depends_on=["T001", "T002"],  # Both exist
        )

        assert result.valid is True

    def test_empty_dependencies_pass(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should pass when no dependencies specified."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_create_guards(
            title="New task",
            task_type="implementation",
            session_id=None,
            depends_on=[],
        )

        assert result.valid is True


# =============================================================================
# TaskGuardService Tests - Parent Validation
# =============================================================================


class TestParentGuards:
    """Tests for parent task validation."""

    def test_nonexistent_parent_fails(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should fail when parent task doesn't exist."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_create_guards(
            title="Child task",
            task_type="implementation",
            session_id=None,
            parent_id="T999",  # Doesn't exist
        )

        assert result.valid is False
        assert any(f.guard == "parent-exists" for f in result.failures)

    def test_valid_parent_passes(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should pass when parent task exists."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_create_guards(
            title="Child task",
            task_type="implementation",
            session_id=None,
            parent_id="T001",  # Exists
        )

        assert result.valid is True

    def test_null_parent_passes(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should pass when no parent specified."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_create_guards(
            title="Root task",
            task_type="implementation",
            session_id=None,
            parent_id=None,
        )

        assert result.valid is True


# =============================================================================
# TaskGuardService Tests - State Transition Validation
# =============================================================================


class TestStateTransitionGuards:
    """Tests for state transition guard checks."""

    def test_todo_to_wip_allowed(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should allow transition from todo to wip."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_transition_guards("T001", "wip")

        assert result.valid is True
        assert result.current_state == "todo"
        assert result.to_state == "wip"

    def test_wip_to_done_allowed(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should allow transition from wip to done."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_transition_guards("T002", "done")

        assert result.valid is True
        assert result.current_state == "wip"
        assert result.to_state == "done"

    def test_done_to_validated_allowed(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should allow transition from done to validated."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_transition_guards("T004", "validated")

        assert result.valid is True
        assert result.current_state == "done"
        assert result.to_state == "validated"

    def test_todo_to_done_not_allowed(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should not allow direct transition from todo to done (must go through wip)."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_transition_guards("T001", "done")

        assert result.valid is False
        assert any(f.guard == "valid-transition" for f in result.failures)

    def test_validated_to_todo_not_allowed(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should not allow backward transition from validated to todo."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_transition_guards("T005", "todo")

        assert result.valid is False
        assert any(f.guard == "valid-transition" for f in result.failures)

    def test_wip_to_blocked_allowed(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should allow transition from wip to blocked."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_transition_guards("T002", "blocked")

        assert result.valid is True

    def test_blocked_to_wip_allowed(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should allow transition from blocked back to wip."""
        # First we need a blocked task
        from services.task_guard import TaskGuardService

        # Create blocked task directly in fixture
        tasks_dir = project_with_guards_setup / ".project" / "tasks" / "blocked"
        (tasks_dir / "T007.md").write_text(
            create_task_frontmatter("T007", "Blocked task")
            + "\n# Task T007\nBlocked."
        )

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_transition_guards("T007", "wip")

        assert result.valid is True

    def test_nonexistent_task_transition_fails(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should fail transition for non-existent task."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_transition_guards("T999", "wip")

        assert result.valid is False
        assert any(f.guard == "task-exists" for f in result.failures)

    def test_invalid_target_state_fails(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should fail for invalid target state."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_transition_guards("T001", "invalid-state")

        assert result.valid is False
        assert any(f.guard == "valid-state" for f in result.failures)


# =============================================================================
# TaskGuardService Tests - Dependency Readiness for Transition
# =============================================================================


class TestTransitionDependencyGuards:
    """Tests for dependency checks during transitions."""

    def test_transition_blocked_by_incomplete_dependency(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should block wip transition if dependencies not complete."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        # T003 depends on T002 which is in wip
        result = service.check_transition_guards("T003", "wip")

        assert result.valid is False
        assert any(f.guard == "dependencies-ready" for f in result.failures)

    def test_transition_allowed_when_dependencies_complete(
        self, project_with_guards_setup: Path
    ) -> None:
        """Should allow wip transition when dependencies are done/validated."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        # T006 depends on T005 which is validated
        result = service.check_transition_guards("T006", "wip")

        assert result.valid is True


# =============================================================================
# TaskGuardService Tests - Guard Result Structure
# =============================================================================


class TestGuardResultStructure:
    """Tests for guard result data structure."""

    def test_create_guard_result_has_required_fields(
        self, project_with_guards_setup: Path
    ) -> None:
        """Create guard result should have valid, failures, and warnings."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_create_guards(
            title="Test",
            task_type="implementation",
            session_id=None,
        )

        assert hasattr(result, "valid")
        assert hasattr(result, "failures")
        assert hasattr(result, "warnings")
        assert isinstance(result.failures, list)
        assert isinstance(result.warnings, list)

    def test_transition_guard_result_has_required_fields(
        self, project_with_guards_setup: Path
    ) -> None:
        """Transition guard result should have state info."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_transition_guards("T001", "wip")

        assert hasattr(result, "valid")
        assert hasattr(result, "current_state")
        assert hasattr(result, "to_state")
        assert hasattr(result, "failures")
        assert hasattr(result, "warnings")

    def test_guard_failure_has_guard_and_reason(
        self, project_with_guards_setup: Path
    ) -> None:
        """Guard failures should have guard name and reason."""
        from services.task_guard import TaskGuardService

        service = TaskGuardService(str(project_with_guards_setup))
        result = service.check_create_guards(
            title="Test",
            task_type="implementation",
            session_id="session-does-not-exist",
        )

        assert len(result.failures) > 0
        failure = result.failures[0]
        assert hasattr(failure, "guard")
        assert hasattr(failure, "reason")
        assert isinstance(failure.guard, str)
        assert isinstance(failure.reason, str)
        assert len(failure.reason) > 0
