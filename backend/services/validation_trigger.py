"""Validation trigger guard service (T042).

Provides guard checks for triggering validation including:
- task-exists: Target task must exist
- task-done: Task must be in 'done' state (not wip, not validated)
- no-active-validation: No active QA round in progress for this task
- validators-valid: Specified validators must exist in catalog (if provided)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from services.qa_reader import QAReaderService
from services.task_reader import TaskReaderService


# Default validator catalog (in production, this would be loaded from config)
VALID_VALIDATORS = frozenset(
    {
        "code-review",
        "test-coverage",
        "security",
        "performance",
        "accessibility",
        "documentation",
        "api-review",
        "database-review",
    }
)

# Default suggested validators when none specified
DEFAULT_VALIDATORS = ["code-review", "test-coverage"]

# QA states that indicate active validation (blocking new triggers)
ACTIVE_QA_STATES = frozenset({"wip", "todo", "waiting"})


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
class TriggerGuardResult:
    """Result of validation trigger guards check."""

    valid: bool
    task_id: str
    task_state: str | None = None
    suggested_validators: list[str] = field(default_factory=list)
    failures: list[GuardFailure] = field(default_factory=list)
    warnings: list[GuardWarning] = field(default_factory=list)


def generate_qa_id(task_id: str) -> str:
    """Generate a unique QA ID for a task.

    Args:
        task_id: The task ID.

    Returns:
        A unique QA ID in format QA-{task_id} or with UUID suffix if needed.
    """
    return f"QA-{task_id}"


def generate_action_id() -> str:
    """Generate a unique action ID for audit entries.

    Returns:
        A unique action ID.
    """
    return str(uuid.uuid4())


class ValidationTriggerGuardService:
    """Service for checking guards on validation trigger operations."""

    def __init__(self, project_path: str) -> None:
        """Initialize the validation trigger guard service.

        Args:
            project_path: Absolute path to the Edison project root.
        """
        self.project_path = Path(project_path)
        self.task_reader = TaskReaderService(project_path)
        self.qa_reader = QAReaderService(project_path)

    def check_trigger_guards(
        self,
        task_id: str,
        validators: list[str] | None = None,
    ) -> TriggerGuardResult:
        """Check guards for triggering validation.

        Args:
            task_id: The task ID to trigger validation for.
            validators: Optional list of validators to use. If None, uses defaults.

        Returns:
            TriggerGuardResult with valid status and any failures/warnings.
        """
        failures: list[GuardFailure] = []
        warnings: list[GuardWarning] = []
        task_state: str | None = None

        # Guard 1: task-exists
        task = self.task_reader.get_task(task_id)
        if task is None:
            failures.append(
                GuardFailure(
                    guard="task-exists",
                    reason=f"Task '{task_id}' does not exist",
                )
            )
            return TriggerGuardResult(
                valid=False,
                task_id=task_id,
                task_state=None,
                suggested_validators=[],
                failures=failures,
                warnings=warnings,
            )

        task_state = task.state

        # Guard 2: task-done
        if task.state != "done":
            failures.append(
                GuardFailure(
                    guard="task-done",
                    reason=f"Task must be in 'done' state to trigger validation. "
                    f"Current state: '{task.state}'",
                )
            )

        # Guard 3: no-active-validation
        qa_records = self.qa_reader.list_qa_records()
        for qa in qa_records:
            if qa.task_id == task_id and qa.state in ACTIVE_QA_STATES:
                failures.append(
                    GuardFailure(
                        guard="no-active-validation",
                        reason=f"Task '{task_id}' already has an active validation "
                        f"in state '{qa.state}'",
                    )
                )
                break

        # Guard 4: validators-valid
        if validators:
            invalid_validators = [v for v in validators if v not in VALID_VALIDATORS]
            if invalid_validators:
                failures.append(
                    GuardFailure(
                        guard="validators-valid",
                        reason=f"Invalid validators: {', '.join(invalid_validators)}. "
                        f"Valid validators are: {', '.join(sorted(VALID_VALIDATORS))}",
                    )
                )

        # Determine suggested validators
        suggested_validators = validators if validators else DEFAULT_VALIDATORS.copy()

        return TriggerGuardResult(
            valid=len(failures) == 0,
            task_id=task_id,
            task_state=task_state,
            suggested_validators=suggested_validators,
            failures=failures,
            warnings=warnings,
        )


class ValidationTriggerService:
    """Service for triggering validation (creating QA records)."""

    def __init__(self, project_path: str) -> None:
        """Initialize the validation trigger service.

        Args:
            project_path: Absolute path to the Edison project root.
        """
        self.project_path = Path(project_path)
        self.project_dir = self.project_path / ".project"
        self.qa_dir = self.project_dir / "qa"
        self.qa_reader = QAReaderService(project_path)

    def trigger_validation(
        self,
        task_id: str,
        validators: list[str] | None = None,
    ) -> tuple[str, int]:
        """Trigger validation for a task by creating a QA record.

        Args:
            task_id: The task ID to trigger validation for.
            validators: Optional list of validators to use.

        Returns:
            Tuple of (qa_id, round_number).
        """
        # Determine round number based on existing QA
        existing_round = self._get_existing_round(task_id)
        round_number = existing_round + 1 if existing_round else 1

        # Generate QA ID
        qa_id = generate_qa_id(task_id)

        # Create QA file in 'waiting' state
        waiting_dir = self.qa_dir / "waiting"
        waiting_dir.mkdir(parents=True, exist_ok=True)

        # Generate QA content
        content = self._generate_qa_content(
            qa_id=qa_id,
            task_id=task_id,
            round_number=round_number,
            validators=validators or DEFAULT_VALIDATORS,
        )

        # Write QA file
        qa_file = waiting_dir / f"{task_id}-qa.md"
        qa_file.write_text(content, encoding="utf-8")

        # Invalidate QA reader cache
        self.qa_reader._qa_cache = None

        return qa_id, round_number

    def _get_existing_round(self, task_id: str) -> int | None:
        """Get the current round number for a task's QA.

        Args:
            task_id: The task ID.

        Returns:
            Current round number or None if no QA exists.
        """
        all_qa = self.qa_reader._load_all_qa()
        qa_record = next((r for r in all_qa if r.task_id == task_id), None)
        return qa_record.round if qa_record else None

    def _generate_qa_content(
        self,
        qa_id: str,
        task_id: str,
        round_number: int,
        validators: list[str],
    ) -> str:
        """Generate QA file content.

        Args:
            qa_id: The QA ID.
            task_id: The task ID.
            round_number: The validation round number.
            validators: List of validators to assign.

        Returns:
            QA markdown content.
        """
        now = datetime.now(timezone.utc).isoformat()
        lines = [
            "---",
            f"id: {qa_id}",
            f"task_id: {task_id}",
            f"round: {round_number}",
            "validators:",
        ]
        for v in validators:
            lines.append(f"  - {v}")
        lines.extend(
            [
                f"created_at: '{now}'",
                f"updated_at: '{now}'",
                "---",
                "",
                f"# QA for {task_id}",
                "",
                f"Validation round {round_number} triggered.",
                "",
                "## Validators",
                "",
            ]
        )
        for v in validators:
            lines.append(f"- [ ] {v}")
        lines.append("")

        return "\n".join(lines)
