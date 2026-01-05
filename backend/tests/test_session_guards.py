"""Tests for session guard service (T041).

RED Phase: These tests verify session operation guards including:
- Session existence validation
- Valid state validation
- State transition validation
- Has-task check for draft->active
- All-work-complete check for active->done
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
def project_with_sessions(tmp_path: Path) -> Path:
    """Create a mock Edison project with various session states for guard testing."""
    project_path = tmp_path / "session-guard-test-project"
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

    # Create a draft session without tasks
    draft_session_dir = sessions_dir / "draft" / "session-draft-no-task"
    draft_session_dir.mkdir()
    draft_session_json = {
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
    (draft_session_dir / "session.json").write_text(json.dumps(draft_session_json))

    # Create draft session task directories
    draft_tasks_dir = draft_session_dir / "tasks"
    draft_tasks_dir.mkdir()
    for state in ["todo", "wip", "blocked", "done", "validated"]:
        (draft_tasks_dir / state).mkdir()

    # Create a draft session WITH tasks
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

    # Create session-scoped task directories
    draft_with_task_tasks_dir = draft_with_task_dir / "tasks"
    draft_with_task_tasks_dir.mkdir()
    for state in ["todo", "wip", "blocked", "done", "validated"]:
        (draft_with_task_tasks_dir / state).mkdir()

    # Add a task to the session
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

    # Create session-scoped task directories for active session
    active_tasks_dir = active_session_dir / "tasks"
    active_tasks_dir.mkdir()
    for state in ["todo", "wip", "blocked", "done", "validated"]:
        (active_tasks_dir / state).mkdir()

    # Add a task in wip state
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

    # Create session-scoped task directories for completed active session
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

    # Create a blocked session
    blocked_session_dir = sessions_dir / "active" / "session-blocked"
    blocked_session_dir.mkdir()
    blocked_session_json = {
        "id": "session-blocked",
        "state": "active",  # Note: "blocked" isn't a standard session state, sessions stay active but can have blocked tasks
        "meta": {
            "createdAt": "2025-12-27T08:00:00Z",
        },
        "git": {
            "baseBranch": "main",
            "branchName": "session/blocked",
        },
        "tasks": {"T103": "blocked"},
    }
    (blocked_session_dir / "session.json").write_text(json.dumps(blocked_session_json))

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

    # Create an abandoned session
    abandoned_session_dir = sessions_dir / "abandoned" / "session-abandoned"
    abandoned_session_dir.mkdir()
    abandoned_session_json = {
        "id": "session-abandoned",
        "state": "abandoned",
        "meta": {
            "createdAt": "2025-12-27T05:00:00Z",
        },
        "git": {
            "baseBranch": "main",
            "branchName": "session/abandoned",
        },
        "tasks": {},
    }
    (abandoned_session_dir / "session.json").write_text(
        json.dumps(abandoned_session_json)
    )

    # Create .git directory
    (project_path / ".git").mkdir()

    return project_path


# =============================================================================
# SessionGuardService Tests - Session Create Guards
# =============================================================================


class TestSessionCreateGuards:
    """Tests for session creation guard checks."""

    def test_create_guards_valid_for_simple_session(
        self, project_with_sessions: Path
    ) -> None:
        """Should allow creating a session with valid parameters."""
        from services.session_guard import SessionGuardService

        service = SessionGuardService(str(project_with_sessions))
        result = service.check_create_guards(
            owner="test-user",
            base_branch="main",
        )

        assert result.valid is True
        assert len(result.failures) == 0

    def test_create_guards_valid_with_null_owner(
        self, project_with_sessions: Path
    ) -> None:
        """Should allow creating a session without owner."""
        from services.session_guard import SessionGuardService

        service = SessionGuardService(str(project_with_sessions))
        result = service.check_create_guards(
            owner=None,
            base_branch="main",
        )

        assert result.valid is True
        assert len(result.failures) == 0


# =============================================================================
# SessionGuardService Tests - Session Transition Guards (Existence)
# =============================================================================


class TestSessionExistenceGuards:
    """Tests for session existence guard checks."""

    def test_transition_fails_for_nonexistent_session(
        self, project_with_sessions: Path
    ) -> None:
        """Should fail transition for non-existent session."""
        from services.session_guard import SessionGuardService

        service = SessionGuardService(str(project_with_sessions))
        result = service.check_transition_guards("session-does-not-exist", "active")

        assert result.valid is False
        assert any(f.guard == "session-exists" for f in result.failures)

    def test_transition_passes_for_existing_session(
        self, project_with_sessions: Path
    ) -> None:
        """Should pass existence check for existing session."""
        from services.session_guard import SessionGuardService

        service = SessionGuardService(str(project_with_sessions))
        result = service.check_transition_guards("session-draft-with-task", "active")

        # Should pass existence check (might fail on other guards)
        assert not any(f.guard == "session-exists" for f in result.failures)


# =============================================================================
# SessionGuardService Tests - Valid State Guards
# =============================================================================


class TestValidStateGuards:
    """Tests for valid state guard checks."""

    def test_transition_fails_for_invalid_target_state(
        self, project_with_sessions: Path
    ) -> None:
        """Should fail for invalid target state."""
        from services.session_guard import SessionGuardService

        service = SessionGuardService(str(project_with_sessions))
        result = service.check_transition_guards(
            "session-draft-with-task", "invalid-state"
        )

        assert result.valid is False
        assert any(f.guard == "valid-state" for f in result.failures)

    def test_transition_passes_for_valid_target_state(
        self, project_with_sessions: Path
    ) -> None:
        """Should pass for valid target state."""
        from services.session_guard import SessionGuardService

        service = SessionGuardService(str(project_with_sessions))
        result = service.check_transition_guards("session-draft-with-task", "active")

        assert not any(f.guard == "valid-state" for f in result.failures)


# =============================================================================
# SessionGuardService Tests - Valid Transition Guards
# =============================================================================


class TestValidTransitionGuards:
    """Tests for valid transition guard checks."""

    def test_draft_to_active_allowed_with_task(
        self, project_with_sessions: Path
    ) -> None:
        """Should allow transition from draft to active when session has task."""
        from services.session_guard import SessionGuardService

        service = SessionGuardService(str(project_with_sessions))
        result = service.check_transition_guards("session-draft-with-task", "active")

        assert result.valid is True
        assert result.current_state == "draft"
        assert result.to_state == "active"

    def test_draft_to_active_blocked_without_task(
        self, project_with_sessions: Path
    ) -> None:
        """Should block transition from draft to active without task."""
        from services.session_guard import SessionGuardService

        service = SessionGuardService(str(project_with_sessions))
        result = service.check_transition_guards("session-draft-no-task", "active")

        assert result.valid is False
        assert any(f.guard == "has-task" for f in result.failures)

    def test_active_to_done_blocked_with_incomplete_tasks(
        self, project_with_sessions: Path
    ) -> None:
        """Should block transition to done when tasks incomplete."""
        from services.session_guard import SessionGuardService

        service = SessionGuardService(str(project_with_sessions))
        # session-active has T101 in wip state
        result = service.check_transition_guards("session-active", "done")

        assert result.valid is False
        assert any(f.guard == "all-work-complete" for f in result.failures)

    def test_active_to_done_allowed_when_all_complete(
        self, project_with_sessions: Path
    ) -> None:
        """Should allow transition to done when all tasks complete."""
        from services.session_guard import SessionGuardService

        service = SessionGuardService(str(project_with_sessions))
        # session-active-complete has T102 in done state
        result = service.check_transition_guards("session-active-complete", "done")

        # Should pass the all-work-complete check
        assert not any(f.guard == "all-work-complete" for f in result.failures)

    def test_active_to_blocked_allowed(self, project_with_sessions: Path) -> None:
        """Should allow transition from active to blocked."""
        from services.session_guard import SessionGuardService

        service = SessionGuardService(str(project_with_sessions))
        result = service.check_transition_guards("session-active", "blocked")

        assert result.valid is True

    def test_completed_session_cannot_transition(
        self, project_with_sessions: Path
    ) -> None:
        """Should block transitions from completed session."""
        from services.session_guard import SessionGuardService

        service = SessionGuardService(str(project_with_sessions))
        result = service.check_transition_guards("session-completed", "active")

        assert result.valid is False
        assert any(f.guard == "valid-transition" for f in result.failures)

    def test_abandoned_session_cannot_transition(
        self, project_with_sessions: Path
    ) -> None:
        """Should block transitions from abandoned session."""
        from services.session_guard import SessionGuardService

        service = SessionGuardService(str(project_with_sessions))
        result = service.check_transition_guards("session-abandoned", "active")

        assert result.valid is False
        assert any(f.guard == "valid-transition" for f in result.failures)

    def test_draft_to_completed_not_allowed(self, project_with_sessions: Path) -> None:
        """Should not allow direct transition from draft to completed."""
        from services.session_guard import SessionGuardService

        service = SessionGuardService(str(project_with_sessions))
        result = service.check_transition_guards("session-draft-with-task", "completed")

        assert result.valid is False
        assert any(f.guard == "valid-transition" for f in result.failures)


# =============================================================================
# SessionGuardService Tests - Guard Result Structure
# =============================================================================


class TestGuardResultStructure:
    """Tests for guard result data structure."""

    def test_create_guard_result_has_required_fields(
        self, project_with_sessions: Path
    ) -> None:
        """Create guard result should have valid, failures, and warnings."""
        from services.session_guard import SessionGuardService

        service = SessionGuardService(str(project_with_sessions))
        result = service.check_create_guards(
            owner="test",
            base_branch="main",
        )

        assert hasattr(result, "valid")
        assert hasattr(result, "failures")
        assert hasattr(result, "warnings")
        assert isinstance(result.failures, list)
        assert isinstance(result.warnings, list)

    def test_transition_guard_result_has_required_fields(
        self, project_with_sessions: Path
    ) -> None:
        """Transition guard result should have state info."""
        from services.session_guard import SessionGuardService

        service = SessionGuardService(str(project_with_sessions))
        result = service.check_transition_guards("session-draft-with-task", "active")

        assert hasattr(result, "valid")
        assert hasattr(result, "current_state")
        assert hasattr(result, "to_state")
        assert hasattr(result, "failures")
        assert hasattr(result, "warnings")

    def test_guard_failure_has_guard_and_reason(
        self, project_with_sessions: Path
    ) -> None:
        """Guard failures should have guard name and reason."""
        from services.session_guard import SessionGuardService

        service = SessionGuardService(str(project_with_sessions))
        result = service.check_transition_guards("session-does-not-exist", "active")

        assert len(result.failures) > 0
        failure = result.failures[0]
        assert hasattr(failure, "guard")
        assert hasattr(failure, "reason")
        assert isinstance(failure.guard, str)
        assert isinstance(failure.reason, str)
        assert len(failure.reason) > 0
