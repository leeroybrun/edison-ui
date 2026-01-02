"""Task reader service (T020/T022).

Reads tasks from Edison project filesystem, computes readiness, and validation status.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


# States that satisfy a dependency (task is considered "done")
COMPLETED_STATES = frozenset({"done", "validated"})

# All valid task states
VALID_STATES = frozenset({"todo", "wip", "blocked", "done", "validated"})


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
        self._qa_cache: dict[str, dict[str, str]] | None = None

    def _parse_frontmatter(self, content: str) -> dict[str, str | list[str] | None]:
        """Parse YAML frontmatter from a markdown file.

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

        for line in frontmatter.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            # Handle quoted strings
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            elif value.startswith('"') and value.endswith('"'):
                value = value[1:-1]

            # Handle JSON arrays
            if value.startswith("[") and value.endswith("]"):
                try:
                    import json

                    result[key] = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    result[key] = value
            else:
                result[key] = value if value else None

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

    def _load_qa_records(self) -> dict[str, dict[str, str]]:
        """Load QA records to determine validation status.

        Returns:
            Dictionary mapping task_id to QA state info.
        """
        if self._qa_cache is not None:
            return self._qa_cache

        qa_records: dict[str, dict[str, str]] = {}

        qa_dir = self.project_dir / "qa"
        if not qa_dir.exists():
            self._qa_cache = qa_records
            return qa_records

        qa_states = ["waiting", "todo", "wip", "done", "validated"]
        for qa_state in qa_states:
            state_dir = qa_dir / qa_state
            if not state_dir.exists():
                continue

            for qa_file in state_dir.glob("*.md"):
                try:
                    content = qa_file.read_text(encoding="utf-8")
                except OSError:
                    continue

                fm = self._parse_frontmatter(content)
                task_id = fm.get("task_id")
                if task_id and isinstance(task_id, str):
                    qa_records[task_id] = {"qa_state": qa_state}

        self._qa_cache = qa_records
        return qa_records

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

    def get_validation_status(self, task_id: str) -> str:
        """Compute the validation status for a task.

        Returns one of:
        - "validated": Task is in validated state
        - "in_progress": Task has QA record in wip
        - "rejected": Task has QA record in done with rejection
        - "needs_validation": Task is in done state without QA
        - "unknown": Task not found or not applicable

        Args:
            task_id: The task ID.

        Returns:
            Validation status string.
        """
        task = self.get_task(task_id)
        if not task:
            return "unknown"

        # If task is in validated state, it's validated
        if task.state == "validated":
            return "validated"

        # Check QA records
        qa_records = self._load_qa_records()
        qa_info = qa_records.get(task_id)

        if qa_info:
            qa_state = qa_info.get("qa_state", "")
            if qa_state == "validated":
                return "validated"
            elif qa_state == "wip":
                return "in_progress"
            elif qa_state == "done":
                # Could check for rejection here
                return "in_progress"
            elif qa_state in ("waiting", "todo"):
                return "needs_validation"

        # If task is done but no QA record, needs validation
        if task.state == "done":
            return "needs_validation"

        # For other states, unknown/not applicable
        return "unknown"

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
                        required_states=list(COMPLETED_STATES),
                        reason=f"Dependency {dep_id} not found",
                    )
                )
                continue

            if dep_task.state not in COMPLETED_STATES:
                blocked_by.append(
                    BlockedByInfo(
                        dependency_id=dep_id,
                        dependency_state=dep_task.state,
                        required_states=list(COMPLETED_STATES),
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
        self._qa_cache = None
