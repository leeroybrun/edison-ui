"""Session context service (T070).

Retrieves session context by shelling out to Edison CLI.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


class EdisonCLIError(Exception):
    """Error from Edison CLI execution."""

    pass


@dataclass
class SessionContext:
    """Session context data."""

    is_edison_project: bool
    project_root: str
    session_id: str
    session_state: str
    worktree_path: str | None
    current_task_id: str | None
    current_task_state: str | None
    active_packs: list[str] = field(default_factory=list)
    constitutions: dict[str, str] = field(default_factory=dict)


class SessionContextService:
    """Service for retrieving session context via Edison CLI."""

    REDACTED_MARKER = "[REDACTED]"

    def __init__(self, project_path: str) -> None:
        """Initialize the session context service.

        Args:
            project_path: Absolute path to the Edison project root.
        """
        self.project_path = Path(project_path)

    def _redact_path(self, path: str | None) -> str | None:
        """Redact a sensitive path.

        Args:
            path: The path to redact.

        Returns:
            Redacted path marker or None.
        """
        if path is None:
            return None
        return self.REDACTED_MARKER

    def get_context(self, session_id: str) -> SessionContext:
        """Get session context from Edison CLI.

        Args:
            session_id: The session ID to get context for.

        Returns:
            SessionContext with computed context data.

        Raises:
            EdisonCLIError: If CLI is unavailable or fails.
        """
        try:
            result = subprocess.run(
                ["edison", "session", "context", session_id, "--json"],
                capture_output=True,
                text=True,
                cwd=str(self.project_path),
                timeout=30,
            )
        except FileNotFoundError:
            raise EdisonCLIError("Edison CLI is unavailable")
        except subprocess.TimeoutExpired:
            raise EdisonCLIError("Edison CLI timed out")

        if result.returncode != 0:
            error_msg = result.stderr or "Unknown error"
            raise EdisonCLIError(f"Edison CLI failed: {error_msg}")

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise EdisonCLIError(f"Failed to parse CLI output: {e}")

        return SessionContext(
            is_edison_project=data.get("isEdisonProject", False),
            project_root=self._redact_path(data.get("projectRoot")) or "",
            session_id=data.get("sessionId", session_id),
            session_state=data.get("sessionState", "unknown"),
            worktree_path=self._redact_path(data.get("worktreePath")),
            current_task_id=data.get("currentTaskId"),
            current_task_state=data.get("currentTaskState"),
            active_packs=data.get("activePacks", []),
            constitutions=data.get("constitutions", {}),
        )
