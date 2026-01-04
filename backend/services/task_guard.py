"""Task guard service (T040).

Provides guard checks for task operations including:
- Session state validation
- Dependency validation
- State transition validation
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from services.session_reader import SessionReaderService
from services.task_reader import TaskReaderService, VALID_STATES, COMPLETED_STATES


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


# Valid state transitions: from_state -> set of allowed to_states
# Based on Edison task lifecycle: todo -> wip -> done -> validated
# With blocked as a side-channel from wip
VALID_TRANSITIONS: dict[str, set[str]] = {
    "todo": {"wip"},
    "wip": {"done", "blocked"},
    "blocked": {"wip", "todo"},
    "done": {"validated", "wip"},  # Allow done->wip for rework
    "validated": set(),  # Terminal state, no transitions allowed
}


class TaskGuardService:
    """Service for checking guards on task operations."""

    def __init__(self, project_path: str) -> None:
        """Initialize the task guard service.

        Args:
            project_path: Absolute path to the Edison project root.
        """
        self.project_path = Path(project_path)
        self.task_reader = TaskReaderService(project_path)
        self.session_reader = SessionReaderService(project_path)

    def check_create_guards(
        self,
        title: str,
        task_type: str,
        session_id: str | None = None,
        parent_id: str | None = None,
        depends_on: list[str] | None = None,
    ) -> CreateGuardResult:
        """Check guards for task creation.

        Args:
            title: Task title.
            task_type: Type of task (implementation, qa, etc.).
            session_id: Optional session ID for session-scoped tasks.
            parent_id: Optional parent task ID.
            depends_on: List of task IDs this task depends on.

        Returns:
            CreateGuardResult with valid status and any failures/warnings.
        """
        failures: list[GuardFailure] = []
        warnings: list[GuardWarning] = []

        # Check session guards if session_id provided
        if session_id is not None:
            session = self.session_reader.get_session(session_id)
            if session is None:
                failures.append(
                    GuardFailure(
                        guard="session-exists",
                        reason=f"Session '{session_id}' does not exist",
                    )
                )
            elif session.state not in ("active", "draft"):
                failures.append(
                    GuardFailure(
                        guard="session-active",
                        reason=f"Cannot create task: session '{session_id}' is {session.state}, must be active or draft",
                    )
                )

        # Check parent exists if specified
        if parent_id is not None:
            parent_task = self.task_reader.get_task(parent_id)
            if parent_task is None:
                failures.append(
                    GuardFailure(
                        guard="parent-exists",
                        reason=f"Parent task '{parent_id}' does not exist",
                    )
                )

        # Check all dependencies exist
        if depends_on:
            for dep_id in depends_on:
                dep_task = self.task_reader.get_task(dep_id)
                if dep_task is None:
                    failures.append(
                        GuardFailure(
                            guard="dependency-exists",
                            reason=f"Dependency task '{dep_id}' does not exist",
                        )
                    )

        return CreateGuardResult(
            valid=len(failures) == 0,
            failures=failures,
            warnings=warnings,
        )

    def check_transition_guards(
        self,
        task_id: str,
        to_state: str,
    ) -> TransitionGuardResult:
        """Check guards for a state transition.

        Args:
            task_id: The task ID to transition.
            to_state: The target state.

        Returns:
            TransitionGuardResult with valid status and any failures/warnings.
        """
        failures: list[GuardFailure] = []
        warnings: list[GuardWarning] = []
        current_state: str | None = None

        # Validate target state is a known state
        if to_state not in VALID_STATES:
            failures.append(
                GuardFailure(
                    guard="valid-state",
                    reason=f"Invalid target state: '{to_state}'. Must be one of: {', '.join(sorted(VALID_STATES))}",
                )
            )
            return TransitionGuardResult(
                valid=False,
                current_state=None,
                to_state=to_state,
                failures=failures,
                warnings=warnings,
            )

        # Check task exists
        task = self.task_reader.get_task(task_id)
        if task is None:
            failures.append(
                GuardFailure(
                    guard="task-exists",
                    reason=f"Task '{task_id}' does not exist",
                )
            )
            return TransitionGuardResult(
                valid=False,
                current_state=None,
                to_state=to_state,
                failures=failures,
                warnings=warnings,
            )

        current_state = task.state

        # Check transition is valid
        allowed_states = VALID_TRANSITIONS.get(current_state, set())
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

        # Check dependencies are ready when transitioning to wip
        if to_state == "wip" and task.depends_on:
            for dep_id in task.depends_on:
                dep_task = self.task_reader.get_task(dep_id)
                if dep_task is None:
                    failures.append(
                        GuardFailure(
                            guard="dependencies-ready",
                            reason=f"Dependency '{dep_id}' does not exist",
                        )
                    )
                elif dep_task.state not in COMPLETED_STATES:
                    failures.append(
                        GuardFailure(
                            guard="dependencies-ready",
                            reason=f"Dependency '{dep_id}' is in state '{dep_task.state}', "
                            f"must be in: {', '.join(sorted(COMPLETED_STATES))}",
                        )
                    )

        return TransitionGuardResult(
            valid=len(failures) == 0,
            current_state=current_state,
            to_state=to_state,
            failures=failures,
            warnings=warnings,
        )
