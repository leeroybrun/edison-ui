"""Session writer service (T041).

Provides filesystem operations for session creation and state transitions.
"""
from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from services.session_reader import SessionReaderService


def generate_session_id() -> str:
    """Generate a unique session ID.

    Returns:
        A unique session ID in format session-{uuid-prefix}.
    """
    # Use UUID and take first 8 chars for readable but unique ID
    unique = uuid.uuid4().hex[:8]
    return f"session-{unique}"


def generate_action_id() -> str:
    """Generate a unique action ID for audit entries.

    Returns:
        A unique action ID.
    """
    return str(uuid.uuid4())


class SessionWriterService:
    """Service for writing session data to the Edison project filesystem."""

    # Known session states (directories under .project/sessions/)
    SESSION_STATES = ["draft", "active", "blocked", "paused", "done", "closing", "completed", "validated", "archived", "abandoned"]

    def __init__(self, project_path: str) -> None:
        """Initialize the session writer service.

        Args:
            project_path: Absolute path to the Edison project root.
        """
        self.project_path = Path(project_path)
        self.project_dir = self.project_path / ".project"
        self.sessions_dir = self.project_dir / "sessions"
        self.session_reader = SessionReaderService(project_path)

    def create_session(
        self,
        owner: str | None = None,
        base_branch: str = "main",
    ) -> str:
        """Create a new session in draft state.

        Args:
            owner: Optional owner of the session.
            base_branch: The base branch for the session.

        Returns:
            The new session ID.
        """
        session_id = generate_session_id()
        now = datetime.now(timezone.utc).isoformat()

        # Create session directory in draft state
        draft_dir = self.sessions_dir / "draft"
        draft_dir.mkdir(parents=True, exist_ok=True)

        session_dir = draft_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Create task directories for the session
        tasks_dir = session_dir / "tasks"
        tasks_dir.mkdir(parents=True, exist_ok=True)
        for state in ["todo", "wip", "blocked", "done", "validated"]:
            (tasks_dir / state).mkdir(parents=True, exist_ok=True)

        # Create session.json
        session_data = {
            "id": session_id,
            "state": "draft",
            "phase": None,
            "meta": {
                "createdAt": now,
                "owner": owner,
            },
            "git": {
                "baseBranch": base_branch,
                "branchName": f"session/{session_id}",
            },
            "tasks": {},
        }

        session_file = session_dir / "session.json"
        session_file.write_text(json.dumps(session_data, indent=2), encoding="utf-8")

        return session_id

    def transition_session(self, session_id: str, to_state: str) -> str:
        """Transition a session to a new state by moving its directory.

        Args:
            session_id: The session ID to transition.
            to_state: The target state.

        Returns:
            The previous state.

        Raises:
            ValueError: If session not found or transition invalid.
        """
        session = self.session_reader.get_session(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        current_state = session.state

        if current_state == to_state:
            # No change needed
            return current_state

        # Find the current session directory
        current_dir = self._find_session_dir(session_id)
        if current_dir is None:
            raise ValueError(f"Session directory for {session_id} not found")

        # Ensure target state directory exists
        target_state_dir = self.sessions_dir / to_state
        target_state_dir.mkdir(parents=True, exist_ok=True)

        # Move session directory to new state
        target_dir = target_state_dir / session_id
        shutil.move(str(current_dir), str(target_dir))

        # Update session.json with new state and lastActive
        self._update_session_state(target_dir, to_state)

        return current_state

    def _find_session_dir(self, session_id: str) -> Path | None:
        """Find the directory for a session.

        Args:
            session_id: The session ID to find.

        Returns:
            Path to session directory or None if not found.
        """
        for state in self.SESSION_STATES:
            state_dir = self.sessions_dir / state
            if not state_dir.exists():
                continue
            session_dir = state_dir / session_id
            if session_dir.exists():
                return session_dir
        return None

    def _update_session_state(self, session_dir: Path, new_state: str) -> None:
        """Update the session.json file with new state.

        Args:
            session_dir: Path to session directory.
            new_state: The new state to set.
        """
        session_file = session_dir / "session.json"
        if not session_file.exists():
            return

        try:
            with open(session_file) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        # Update state
        data["state"] = new_state

        # Update lastActive timestamp
        now = datetime.now(timezone.utc).isoformat()
        if "meta" not in data:
            data["meta"] = {}
        data["meta"]["lastActive"] = now

        # Write back
        session_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
