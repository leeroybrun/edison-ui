"""Session guard service (T041).

Provides guard checks for session operations including:
- Session existence validation
- Valid state validation
- State transition validation
- Has-task check for draft->active
- All-work-complete check for active->done
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from services.session_reader import SessionReaderService
from services.task_reader import TaskReaderService


@dataclass
class GuardFailure:
    """A guard check that failed."""

    guard: str
    reason: str


@dataclass
class GuardWarning:
    """A warning from a guard check (non-blocking)."""

    guard: str
    message: str


@dataclass
class CreateGuardResult:
    """Result of create guards check."""

    valid: bool
    failures: list[GuardFailure] = field(default_factory=list)
    warnings: list[GuardWarning] = field(default_factory=list)


@dataclass
class TransitionGuardResult:
    """Result of transition guards check."""

    valid: bool
    current_state: str | None = None
    to_state: str | None = None
    failures: list[GuardFailure] = field(default_factory=list)
    warnings: list[GuardWarning] = field(default_factory=list)


# Valid session states
VALID_SESSION_STATES = {
    "draft",
    "active",
    "blocked",
    "paused",
    "done",
    "closing",
    "completed",
    "validated",
    "archived",
    "abandoned",
}

# Valid state transitions: from_state -> set of allowed to_states
# Based on Edison session lifecycle
VALID_SESSION_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"active"},  # Draft can only activate (with task)
    "active": {
        "done",
        "blocked",
        "closing",
        "paused",
    },  # Active can complete, block, close, or pause
    "blocked": {"active"},  # Blocked can unblock to active
    "paused": {"active", "abandoned"},  # Paused can resume or abandon
    "done": {"validated"},  # Done can be validated
    "closing": {"validated"},  # Closing can be validated
    "validated": {"archived"},  # Validated can be archived
    "completed": set(),  # Terminal state (legacy)
    "archived": set(),  # Terminal state
    "abandoned": set(),  # Terminal state
}

# States considered "complete" for tasks
COMPLETED_TASK_STATES = {"done", "validated"}


class SessionGuardService:
    """Service for checking guards on session operations."""

    def __init__(self, project_path: str) -> None:
        """Initialize the session guard service.

        Args:
            project_path: Absolute path to the Edison project root.
        """
        self.project_path = Path(project_path)
        self.session_reader = SessionReaderService(project_path)

    def check_create_guards(
        self,
        owner: str | None = None,
        base_branch: str = "main",
    ) -> CreateGuardResult:
        """Check guards for session creation.

        Args:
            owner: Optional owner of the session.
            base_branch: The base branch for the session.

        Returns:
            CreateGuardResult with valid status and any failures/warnings.
        """
        failures: list[GuardFailure] = []
        warnings: list[GuardWarning] = []

        # Currently no guards that would fail session creation
        # Future guards could include:
        # - Check for existing active sessions (if only one allowed)
        # - Validate base_branch exists in git
        # - Check owner permissions

        return CreateGuardResult(
            valid=len(failures) == 0,
            failures=failures,
            warnings=warnings,
        )

    def check_transition_guards(
        self,
        session_id: str,
        to_state: str,
    ) -> TransitionGuardResult:
        """Check guards for a session state transition.

        Args:
            session_id: The session ID to transition.
            to_state: The target state.

        Returns:
            TransitionGuardResult with valid status and any failures/warnings.
        """
        failures: list[GuardFailure] = []
        warnings: list[GuardWarning] = []
        current_state: str | None = None

        # Validate target state is a known state
        if to_state not in VALID_SESSION_STATES:
            failures.append(
                GuardFailure(
                    guard="valid-state",
                    reason=f"Invalid target state: '{to_state}'. Must be one of: {', '.join(sorted(VALID_SESSION_STATES))}",
                )
            )
            return TransitionGuardResult(
                valid=False,
                current_state=None,
                to_state=to_state,
                failures=failures,
                warnings=warnings,
            )

        # Check session exists
        session = self.session_reader.get_session(session_id)
        if session is None:
            failures.append(
                GuardFailure(
                    guard="session-exists",
                    reason=f"Session '{session_id}' does not exist",
                )
            )
            return TransitionGuardResult(
                valid=False,
                current_state=None,
                to_state=to_state,
                failures=failures,
                warnings=warnings,
            )

        current_state = session.state

        # Check transition is valid
        allowed_states = VALID_SESSION_TRANSITIONS.get(current_state, set())
        if to_state not in allowed_states:
            failures.append(
                GuardFailure(
                    guard="valid-transition",
                    reason=f"Cannot transition from '{current_state}' to '{to_state}'. "
                    f"Allowed transitions from '{current_state}': {', '.join(sorted(allowed_states)) or 'none'}",
                )
            )
            return TransitionGuardResult(
                valid=False,
                current_state=current_state,
                to_state=to_state,
                failures=failures,
                warnings=warnings,
            )

        # Guard: draft -> active requires at least one task
        if current_state == "draft" and to_state == "active":
            if session.task_count == 0:
                failures.append(
                    GuardFailure(
                        guard="has-task",
                        reason="Cannot activate session without at least one linked task",
                    )
                )

        # Guard: active -> done requires all tasks complete
        if current_state == "active" and to_state == "done":
            incomplete_tasks = self._get_incomplete_session_tasks(session_id)
            if incomplete_tasks:
                failures.append(
                    GuardFailure(
                        guard="all-work-complete",
                        reason=f"Cannot complete session: {len(incomplete_tasks)} task(s) not done/validated: {', '.join(incomplete_tasks[:5])}",
                    )
                )

        return TransitionGuardResult(
            valid=len(failures) == 0,
            current_state=current_state,
            to_state=to_state,
            failures=failures,
            warnings=warnings,
        )

    def _get_incomplete_session_tasks(self, session_id: str) -> list[str]:
        """Get list of incomplete task IDs for a session.

        Args:
            session_id: The session ID to check.

        Returns:
            List of task IDs that are not in completed states.
        """
        incomplete: list[str] = []
        task_reader = TaskReaderService(str(self.project_path))

        # Get all tasks for this session
        tasks = task_reader.list_tasks(session_id=session_id)

        for task in tasks:
            if task.state not in COMPLETED_TASK_STATES:
                incomplete.append(task.task_id)

        return incomplete
