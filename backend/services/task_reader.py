"""Task reader service (T020/T022).

Reads tasks from Edison project filesystem, computes readiness, and validation status.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from services.qa_reader import QAReaderService


# States that satisfy a dependency (task is considered "done")
# Use tuple for deterministic ordering in API responses
COMPLETED_STATES_LIST = ("done", "validated")
COMPLETED_STATES = frozenset(COMPLETED_STATES_LIST)

# All valid task states
VALID_STATES = frozenset({"todo", "wip", "blocked", "done", "validated"})


@dataclass
class ValidationSummaryInfo:
    """Summary of validation status."""

    status: str  # none, pending, passed, failed
    last_round: int | None
    validator_count: int
    last_updated: str


@dataclass
class BlockedByInfo:
    """Information about a blocking dependency."""

    dependency_id: str
    dependency_state: str
    required_states: list[str]
    reason: str


@dataclass
class TaskReadiness:
    """Computed readiness for a task."""

    task_id: str
    ready: bool
    blocked_by: list[BlockedByInfo] = field(default_factory=list)
    guard_blocks: list[dict[str, str]] = field(default_factory=list)


@dataclass
class TaskData:
    """Parsed task data from filesystem."""

    task_id: str
    title: str
    state: str
    session_id: str | None = None
    parent_id: str | None = None
    child_ids: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    blocks_tasks: list[str] = field(default_factory=list)
    owner: str | None = None
    tags: list[str] = field(default_factory=list)
    priority: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    file_path: str | None = None


class TaskReaderService:
    """Service for reading and analyzing tasks from Edison project filesystem."""

    def __init__(self, project_path: str) -> None:
        """Initialize the task reader service.

        Args:
            project_path: Absolute path to the Edison project root.
        """
        self.project_path = Path(project_path)
        self.project_dir = self.project_path / ".project"
        self._task_cache: dict[str, TaskData] | None = None
        self.qa_service = QAReaderService(project_path)

    def _parse_frontmatter(self, content: str) -> dict[str, str | list[str] | None]:
        """Parse YAML frontmatter from a markdown file.

        Supports both inline YAML arrays ([a, b]) and block sequences (- item).

        Args:
            content: The file content.

        Returns:
            Dictionary of frontmatter values.
        """
        result: dict[str, str | list[str] | None] = {}

        # Match YAML frontmatter between --- delimiters
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return result

        frontmatter = match.group(1)
        lines = frontmatter.split("\n")
        current_key: str | None = None
        current_list: list[str] | None = None

        for line in lines:
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                continue

            # Check if this is a list item (starts with "- ")
            if stripped.startswith("- ") and current_key is not None:
                if current_list is None:
                    current_list = []
                # Get the item value, stripping quotes if present
                item = stripped[2:].strip()
                if (item.startswith("'") and item.endswith("'")) or (
                    item.startswith('"') and item.endswith('"')
                ):
                    item = item[1:-1]
                current_list.append(item)
                result[current_key] = current_list
                continue

            # Check if this is a key: value line
            if ":" not in line:
                continue

            # Save any accumulated list before processing new key
            if current_list is not None:
                current_list = None

            # Split only on first colon to handle values with colons
            colon_idx = line.index(":")
            key = line[:colon_idx].strip()
            value = line[colon_idx + 1 :].strip()

            current_key = key
            current_list = None

            # Handle quoted strings
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            elif value.startswith('"') and value.endswith('"'):
                value = value[1:-1]

            # Handle JSON/inline YAML arrays like [a, b, c]
            if value.startswith("[") and value.endswith("]"):
                try:
                    import json

                    result[key] = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    # Try parsing as YAML-style inline list
                    inner = value[1:-1]
                    items = [i.strip().strip("'\"") for i in inner.split(",") if i.strip()]
                    result[key] = items if items else value
            elif value:
                result[key] = value
            else:
                # Empty value - might be followed by block sequence
                result[key] = None

        return result

    def _parse_task_file(self, file_path: Path, state: str) -> TaskData | None:
        """Parse a task markdown file.

        Args:
            file_path: Path to the task file.
            state: The task state (derived from directory).

        Returns:
            TaskData or None if parsing fails.
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError:
            return None

        fm = self._parse_frontmatter(content)

        task_id = fm.get("id")
        if not task_id or not isinstance(task_id, str):
            # Fallback to filename stem
            task_id = file_path.stem

        title = fm.get("title", task_id)
        if not isinstance(title, str):
            title = str(title)

        # Parse list fields
        depends_on = fm.get("depends_on", [])
        if isinstance(depends_on, str):
            depends_on = [d.strip() for d in depends_on.split(",") if d.strip()]
        elif not isinstance(depends_on, list):
            depends_on = []

        child_ids = fm.get("child_ids", [])
        if isinstance(child_ids, str):
            child_ids = [c.strip() for c in child_ids.split(",") if c.strip()]
        elif not isinstance(child_ids, list):
            child_ids = []

        blocks_tasks = fm.get("blocks_tasks", [])
        if isinstance(blocks_tasks, str):
            blocks_tasks = [b.strip() for b in blocks_tasks.split(",") if b.strip()]
        elif not isinstance(blocks_tasks, list):
            blocks_tasks = []

        tags = fm.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        elif not isinstance(tags, list):
            tags = []

        parent_id_raw = fm.get("parent_id")
        parent_id: str | None = None
        if parent_id_raw is not None:
            parent_id = str(parent_id_raw) if not isinstance(parent_id_raw, str) else parent_id_raw

        session_id_raw = fm.get("session_id")
        session_id: str | None = None
        if session_id_raw is not None:
            session_id = str(session_id_raw) if not isinstance(session_id_raw, str) else session_id_raw

        owner_raw = fm.get("owner")
        owner: str | None = None
        if owner_raw is not None:
            owner = str(owner_raw) if not isinstance(owner_raw, str) else owner_raw

        priority_raw = fm.get("priority")
        priority: str | None = None
        if priority_raw is not None:
            priority = str(priority_raw) if not isinstance(priority_raw, str) else priority_raw

        created_at_raw = fm.get("created_at")
        created_at: str | None = None
        if created_at_raw is not None:
            created_at = str(created_at_raw) if not isinstance(created_at_raw, str) else created_at_raw

        updated_at_raw = fm.get("updated_at")
        updated_at: str | None = None
        if updated_at_raw is not None:
            updated_at = str(updated_at_raw) if not isinstance(updated_at_raw, str) else updated_at_raw

        return TaskData(
            task_id=task_id,
            title=title,
            state=state,
            session_id=session_id,
            parent_id=parent_id,
            child_ids=child_ids,
            depends_on=depends_on,
            blocks_tasks=blocks_tasks,
            owner=owner,
            tags=tags,
            priority=priority,
            created_at=created_at,
            updated_at=updated_at,
            file_path=str(file_path),
        )

    def _scan_tasks_in_directory(
        self, tasks_dir: Path, session_id: str | None = None
    ) -> list[TaskData]:
        """Scan a tasks directory for task files.

        Args:
            tasks_dir: Path to the tasks directory.
            session_id: Optional session ID for session-scoped tasks.

        Returns:
            List of parsed tasks.
        """
        tasks: list[TaskData] = []

        if not tasks_dir.exists():
            return tasks

        for state in VALID_STATES:
            state_dir = tasks_dir / state
            if not state_dir.exists():
                continue

            for task_file in state_dir.glob("*.md"):
                task = self._parse_task_file(task_file, state)
                if task:
                    # Override session_id if provided (for session-scoped tasks)
                    if session_id and not task.session_id:
                        task.session_id = session_id
                    tasks.append(task)

        return tasks

    def _load_all_tasks(self) -> dict[str, TaskData]:
        """Load all tasks from the project, including session-scoped tasks.

        Returns:
            Dictionary mapping task_id to TaskData.
        """
        if self._task_cache is not None:
            return self._task_cache

        tasks: dict[str, TaskData] = {}

        # Scan global tasks
        global_tasks_dir = self.project_dir / "tasks"
        for task in self._scan_tasks_in_directory(global_tasks_dir):
            tasks[task.task_id] = task

        # Scan session-scoped tasks
        sessions_dir = self.project_dir / "sessions"
        if sessions_dir.exists():
            for state_dir in sessions_dir.iterdir():
                if not state_dir.is_dir():
                    continue
                for session_dir in state_dir.iterdir():
                    if not session_dir.is_dir():
                        continue
                    session_id = session_dir.name
                    session_tasks_dir = session_dir / "tasks"
                    for task in self._scan_tasks_in_directory(
                        session_tasks_dir, session_id=session_id
                    ):
                        tasks[task.task_id] = task

        self._task_cache = tasks
        return tasks

    def list_tasks(
        self,
        session_id: str | None = None,
        states: list[str] | None = None,
        validation_status: str | None = None,
        parent_id: str | None = None,
        search: str | None = None,
    ) -> list[TaskData]:
        """List tasks with optional filtering.

        Args:
            session_id: Filter by session ID. Use "none" for unscoped tasks.
            states: Filter by task states.
            validation_status: Filter by validation status.
            parent_id: Filter by parent task ID.
            search: Search in task title.

        Returns:
            List of matching tasks.
        """
        all_tasks = self._load_all_tasks()
        result: list[TaskData] = []

        for task in all_tasks.values():
            # Filter by session_id
            if session_id is not None:
                if session_id == "none":
                    if task.session_id is not None:
                        continue
                elif task.session_id != session_id:
                    continue

            # Filter by states
            if states and task.state not in states:
                continue

            # Filter by parent_id
            if parent_id and task.parent_id != parent_id:
                continue

            # Filter by validation status
            if validation_status:
                task_vs = self.get_validation_status(task.task_id)
                if task_vs != validation_status:
                    continue

            # Filter by search term
            if search:
                if search.lower() not in task.title.lower():
                    continue

            result.append(task)

        return result

    def get_task(self, task_id: str) -> TaskData | None:
        """Get a specific task by ID.

        Args:
            task_id: The task ID to look up.

        Returns:
            TaskData or None if not found.
        """
        all_tasks = self._load_all_tasks()
        return all_tasks.get(task_id)

    def get_validation_summary(self, task_id: str) -> ValidationSummaryInfo:
        """Compute the validation summary for a task.

        Status values per spec (data-model.md):
        - needs_validation: Task has no QA or needs validation
        - in_progress: QA exists but not yet completed
        - validated: QA passed/approved
        - rejected: QA failed/rejected
        - unknown: Unable to determine status

        Args:
            task_id: The task ID.

        Returns:
            Validation summary info.
        """
        all_qa = self.qa_service._load_all_qa()
        qa_record = next((r for r in all_qa if r.task_id == task_id), None)

        if not qa_record:
            return ValidationSummaryInfo(
                status="needs_validation",
                last_round=None,
                validator_count=0,
                last_updated="1970-01-01T00:00:00Z",
            )

        status = "in_progress"
        # Determine status based on QA state and verdict
        if qa_record.state == "validated":
            status = "validated"
        elif qa_record.verdict:
            v = qa_record.verdict.lower()
            if v in ("pass", "passed", "approved"):
                status = "validated"
            elif v in ("fail", "failed", "reject", "rejected"):
                status = "rejected"
            else:
                status = "in_progress"
        else:
            status = "in_progress"

        return ValidationSummaryInfo(
            status=status,
            last_round=qa_record.round,
            validator_count=len(qa_record.validators),
            last_updated=qa_record.updated_at,
        )

    def get_validation_status(self, task_id: str) -> str:
        """Compute the validation status for a task.

        Returns one of: needs_validation, in_progress, validated, rejected, unknown.

        Args:
            task_id: The task ID.

        Returns:
            Validation status string.
        """
        return self.get_validation_summary(task_id).status

    def compute_readiness(self, task_id: str) -> TaskReadiness:
        """Compute the readiness status for a task.

        A task is ready if all its dependencies are in completed states
        (done or validated).

        Args:
            task_id: The task ID.

        Returns:
            TaskReadiness with blocking information.

        Raises:
            ValueError: If task is not found.
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        blocked_by: list[BlockedByInfo] = []

        # Check each dependency
        for dep_id in task.depends_on:
            dep_task = self.get_task(dep_id)
            if not dep_task:
                # Dependency not found - treat as blocking
                blocked_by.append(
                    BlockedByInfo(
                        dependency_id=dep_id,
                        dependency_state="unknown",
                        required_states=list(COMPLETED_STATES_LIST),
                        reason=f"Dependency {dep_id} not found",
                    )
                )
                continue

            if dep_task.state not in COMPLETED_STATES:
                blocked_by.append(
                    BlockedByInfo(
                        dependency_id=dep_id,
                        dependency_state=dep_task.state,
                        required_states=list(COMPLETED_STATES_LIST),
                        reason=f"Dependency {dep_id} must be done or validated",
                    )
                )

        ready = len(blocked_by) == 0

        return TaskReadiness(
            task_id=task_id,
            ready=ready,
            blocked_by=blocked_by,
            guard_blocks=[],
        )

    def invalidate_cache(self) -> None:
        """Clear the internal cache to force reload on next access."""
        self._task_cache = None
        # Invalidate QA cache too
        self.qa_service._qa_cache = None
