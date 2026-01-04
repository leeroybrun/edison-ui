"""Task writer service (T040).

Provides filesystem operations for task creation and state transitions.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from services.task_reader import TaskReaderService


def generate_task_id() -> str:
    """Generate a unique task ID.

    Returns:
        A unique task ID in format T followed by 6 alphanumeric chars.
    """
    # Use UUID and take first 6 chars for short but unique ID
    unique = uuid.uuid4().hex[:6].upper()
    return f"T{unique}"


def generate_action_id() -> str:
    """Generate a unique action ID for audit entries.

    Returns:
        A unique action ID.
    """
    return str(uuid.uuid4())


class TaskWriterService:
    """Service for writing task files to the Edison project filesystem."""

    def __init__(self, project_path: str) -> None:
        """Initialize the task writer service.

        Args:
            project_path: Absolute path to the Edison project root.
        """
        self.project_path = Path(project_path)
        self.project_dir = self.project_path / ".project"
        self.task_reader = TaskReaderService(project_path)

    def _get_tasks_dir(self, session_id: str | None = None) -> Path:
        """Get the tasks directory for global or session-scoped tasks.

        Args:
            session_id: Optional session ID for session-scoped tasks.

        Returns:
            Path to the tasks directory.
        """
        if session_id:
            # Find session directory
            sessions_dir = self.project_dir / "sessions"
            for state_dir in sessions_dir.iterdir():
                if not state_dir.is_dir():
                    continue
                session_dir = state_dir / session_id
                if session_dir.exists():
                    return session_dir / "tasks"
            # Session not found - this shouldn't happen if guards passed
            raise ValueError(f"Session {session_id} not found")
        return self.project_dir / "tasks"

    def _generate_frontmatter(
        self,
        task_id: str,
        title: str,
        task_type: str,
        session_id: str | None = None,
        parent_id: str | None = None,
        depends_on: list[str] | None = None,
    ) -> str:
        """Generate YAML frontmatter for a task file.

        Args:
            task_id: The task ID.
            title: The task title.
            task_type: The task type.
            session_id: Optional session ID.
            parent_id: Optional parent task ID.
            depends_on: Optional list of dependency task IDs.

        Returns:
            YAML frontmatter string.
        """
        now = datetime.now(timezone.utc).isoformat()
        lines = [
            "---",
            f"id: {task_id}",
            f"title: \"{title}\"",
            f"type: {task_type}",
        ]
        if session_id:
            lines.append(f"session_id: {session_id}")
        if parent_id:
            lines.append(f"parent_id: {parent_id}")
        if depends_on:
            # Format as YAML array
            lines.append("depends_on:")
            for dep in depends_on:
                lines.append(f"  - {dep}")
        lines.append(f"created_at: '{now}'")
        lines.append(f"updated_at: '{now}'")
        lines.append("---")
        return "\n".join(lines)

    def create_task(
        self,
        title: str,
        task_type: str,
        session_id: str | None = None,
        parent_id: str | None = None,
        depends_on: list[str] | None = None,
    ) -> str:
        """Create a new task file.

        Args:
            title: The task title.
            task_type: The task type.
            session_id: Optional session ID for session-scoped tasks.
            parent_id: Optional parent task ID.
            depends_on: Optional list of dependency task IDs.

        Returns:
            The new task ID.
        """
        task_id = generate_task_id()
        tasks_dir = self._get_tasks_dir(session_id)
        todo_dir = tasks_dir / "todo"

        # Ensure directory exists
        todo_dir.mkdir(parents=True, exist_ok=True)

        # Generate content
        frontmatter = self._generate_frontmatter(
            task_id=task_id,
            title=title,
            task_type=task_type,
            session_id=session_id,
            parent_id=parent_id,
            depends_on=depends_on,
        )
        content = f"{frontmatter}\n\n# {title}\n\nTask description goes here.\n"

        # Write file
        task_file = todo_dir / f"{task_id}.md"
        task_file.write_text(content, encoding="utf-8")

        # Invalidate reader cache
        self.task_reader.invalidate_cache()

        return task_id

    def transition_task(self, task_id: str, to_state: str) -> str:
        """Transition a task to a new state by moving its file.

        Args:
            task_id: The task ID to transition.
            to_state: The target state.

        Returns:
            The previous state.

        Raises:
            ValueError: If task not found.
        """
        task = self.task_reader.get_task(task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")

        if task.file_path is None:
            raise ValueError(f"Task {task_id} has no file path")

        current_file = Path(task.file_path)
        current_state = task.state

        if current_state == to_state:
            # No change needed
            return current_state

        # Determine target directory
        # The file is in .project/tasks/{state}/ or .project/sessions/{state}/{session_id}/tasks/{state}/
        # We need to find the tasks base dir and then target state dir
        current_state_dir = current_file.parent
        tasks_base_dir = current_state_dir.parent
        target_state_dir = tasks_base_dir / to_state

        # Ensure target directory exists
        target_state_dir.mkdir(parents=True, exist_ok=True)

        # Move file
        target_file = target_state_dir / current_file.name
        current_file.rename(target_file)

        # Update the updated_at timestamp in the file
        self._update_timestamp(target_file)

        # Invalidate reader cache
        self.task_reader.invalidate_cache()

        return current_state

    def _update_timestamp(self, file_path: Path) -> None:
        """Update the updated_at field in a task file.

        Args:
            file_path: Path to the task file.
        """
        content = file_path.read_text(encoding="utf-8")
        now = datetime.now(timezone.utc).isoformat()

        # Simple replacement of updated_at line
        lines = content.split("\n")
        new_lines = []
        for line in lines:
            if line.startswith("updated_at:"):
                new_lines.append(f"updated_at: '{now}'")
            else:
                new_lines.append(line)

        file_path.write_text("\n".join(new_lines), encoding="utf-8")
