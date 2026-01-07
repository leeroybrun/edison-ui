"""Session next service (T070).

Retrieves session next recommendation by shelling out to Edison CLI.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# Reuse the EdisonCLIError from session_context to ensure consistent exception handling
from services.session_context import EdisonCLIError


@dataclass
class SuggestedAction:
    """A suggested action from the next recommendation."""

    action_type: str
    task_id: str | None = None
    reason: str = ""


@dataclass
class SessionNext:
    """Session next recommendation data."""

    session_id: str
    recommendation: str
    suggested_actions: list[SuggestedAction] = field(default_factory=list)
    timestamp: str = ""


class SessionNextService:
    """Service for retrieving session next recommendation via Edison CLI."""

    def __init__(self, project_path: str) -> None:
        """Initialize the session next service.

        Args:
            project_path: Absolute path to the Edison project root.
        """
        self.project_path = Path(project_path)

    def get_next(self, session_id: str) -> SessionNext:
        """Get session next recommendation from Edison CLI.

        Args:
            session_id: The session ID to get next recommendation for.

        Returns:
            SessionNext with recommendation data.

        Raises:
            EdisonCLIError: If CLI is unavailable or fails.
        """
        try:
            result = subprocess.run(
                ["edison", "session", "next", session_id, "--json"],
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

        # Parse suggested actions from CLI "actions" array
        # CLI format: {"id": "task.claim", "entity": "task", "rationale": "...", ...}
        suggested_actions = []
        for action_data in data.get("actions", []):
            # Map CLI action format to our SuggestedAction
            action_id = action_data.get("id", "")
            suggested_actions.append(
                SuggestedAction(
                    action_type=action_id,
                    task_id=action_data.get("recordId"),
                    reason=action_data.get("rationale", ""),
                )
            )

        # CLI returns "recommendations" array instead of single "recommendation"
        recommendations = data.get("recommendations", [])
        recommendation_text = "\n".join(recommendations) if recommendations else ""

        # If no recommendation but we have a summary, use that
        if not recommendation_text and data.get("summary"):
            recommendation_text = data.get("summary", "")

        return SessionNext(
            session_id=data.get("sessionId", session_id),
            recommendation=recommendation_text,
            suggested_actions=suggested_actions,
            timestamp=data.get("timestamp", ""),
        )
