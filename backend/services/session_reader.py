"""Session reader service (T021).

Reads session data from Edison project filesystem structure.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SessionGitInfo:
    """Git information for a session."""

    branch_name: str | None = None
    base_branch: str = "main"


@dataclass
class Session:
    """A session read from disk."""

    session_id: str
    state: str
    phase: str | None = None
    owner: str | None = None
    task_count: int = 0
    created_at: str = ""
    last_active_at: str | None = None
    git: SessionGitInfo = field(default_factory=SessionGitInfo)


class SessionReaderService:
    """Service for reading session data from an Edison project."""

    # Known session states (directories under .project/sessions/)
    # Must match session_guard.VALID_SESSION_STATES
    SESSION_STATES = [
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
    ]

    def __init__(self, project_path: str) -> None:
        """Initialize the session reader service.

        Args:
            project_path: Absolute path to the Edison project root.
        """
        self.project_path = Path(project_path)
        self.sessions_dir = self.project_path / ".project" / "sessions"

    def _parse_session_json(self, session_file: Path, state: str) -> Session | None:
        """Parse a session.json file into a Session object.

        Args:
            session_file: Path to the session.json file.
            state: The session state (from directory name).

        Returns:
            Parsed Session or None if parsing fails.
        """
        try:
            with open(session_file) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        # Extract session ID
        session_id = data.get("id", "")
        if not session_id:
            return None

        # Extract meta information
        meta = data.get("meta", {})
        owner = meta.get("owner")
        created_at = meta.get("createdAt", "")
        last_active = meta.get("lastActive")

        # Extract phase
        phase = data.get("phase")

        # Extract git information
        git_data = data.get("git", {})
        git_info = SessionGitInfo(
            branch_name=git_data.get("branchName"),
            base_branch=git_data.get("baseBranch", "main"),
        )

        # Calculate task count from tasks index
        tasks = data.get("tasks", {})
        task_count = len(tasks)

        return Session(
            session_id=session_id,
            state=state,
            phase=phase,
            owner=owner,
            task_count=task_count,
            created_at=created_at,
            last_active_at=last_active,
            git=git_info,
        )

    def list_sessions(self, state: str | None = None) -> list[Session]:
        """List all sessions from the project.

        Args:
            state: Optional filter by session state. Must be one of SESSION_STATES.

        Returns:
            List of sessions.

        Raises:
            ValueError: If state is not a valid session state.
        """
        sessions: list[Session] = []

        if not self.sessions_dir.exists():
            return sessions

        # Validate state parameter to prevent directory traversal
        if state is not None and state not in self.SESSION_STATES:
            raise ValueError(
                f"Invalid session state: '{state}'. "
                f"Must be one of: {', '.join(self.SESSION_STATES)}"
            )

        # Determine which states to scan
        states_to_scan = [state] if state else self.SESSION_STATES

        for session_state in states_to_scan:
            state_dir = self.sessions_dir / session_state
            if not state_dir.exists():
                continue

            # Iterate through session directories
            for session_dir in state_dir.iterdir():
                if not session_dir.is_dir():
                    continue

                session_file = session_dir / "session.json"
                if not session_file.exists():
                    continue

                session = self._parse_session_json(session_file, session_state)
                if session:
                    sessions.append(session)

        return sessions

    def get_session(self, session_id: str) -> Session | None:
        """Get a specific session by ID.

        Args:
            session_id: The session ID to look up.

        Returns:
            The session or None if not found.
        """
        sessions = self.list_sessions()
        for session in sessions:
            if session.session_id == session_id:
                return session
        return None
