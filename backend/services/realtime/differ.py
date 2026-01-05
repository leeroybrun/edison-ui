"""Differ for realtime updates (T051).

Computes entity data from file changes for realtime updates.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from services.realtime.watcher import ChangeEvent, ChangeType, EntityType


@dataclass
class DiffResult:
    """Result of processing a change event.

    Contains the entity data to be published.
    """

    entity_type: EntityType
    entity_id: str
    change_type: ChangeType
    data: dict[str, Any] | None


class Differ:
    """Computes entity data from file changes.

    Reads the current file content and extracts entity data.
    """

    def __init__(self, project_path: str) -> None:
        """Initialize the differ.

        Args:
            project_path: Path to the Edison project.
        """
        self.project_path = Path(project_path)

    def process_change(self, event: ChangeEvent) -> DiffResult | None:
        """Process a change event and return the diff result.

        Args:
            event: The change event to process.

        Returns:
            DiffResult with entity data, or None if the change should be ignored.
        """
        # For deletions, return result with no data
        if event.change_type == ChangeType.DELETED:
            return DiffResult(
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                change_type=ChangeType.DELETED,
                data=None,
            )

        # For creates/modifies, try to read the file
        file_path = Path(event.path)
        if not file_path.exists():
            # File was deleted between detection and processing
            return DiffResult(
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                change_type=ChangeType.DELETED,
                data=None,
            )

        # Extract entity data based on type
        data = self._extract_entity_data(event.entity_type, event.entity_id, file_path)

        return DiffResult(
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            change_type=event.change_type,
            data=data,
        )

    def _extract_entity_data(
        self, entity_type: EntityType, entity_id: str, file_path: Path
    ) -> dict[str, Any] | None:
        """Extract entity data from a file.

        Args:
            entity_type: Type of entity.
            entity_id: ID of the entity.
            file_path: Path to the file.

        Returns:
            Entity data dict, or None if extraction fails.
        """
        try:
            if entity_type == EntityType.TASK:
                return self._extract_task_data(entity_id, file_path)
            elif entity_type == EntityType.SESSION:
                return self._extract_session_data(entity_id, file_path)
            elif entity_type == EntityType.QA:
                return self._extract_qa_data(entity_id, file_path)
        except Exception:
            # If extraction fails, return minimal data
            pass

        return {"id": entity_id}

    def _extract_task_data(self, entity_id: str, file_path: Path) -> dict[str, Any]:
        """Extract task data from markdown file.

        Args:
            entity_id: Task ID.
            file_path: Path to task file.

        Returns:
            Task data dict.
        """
        content = file_path.read_text()
        data: dict[str, Any] = {"task_id": entity_id}

        # Parse frontmatter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                for line in frontmatter.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip()
                        value = value.strip().strip("'\"")
                        if key == "id":
                            data["task_id"] = value
                        elif key == "title":
                            data["title"] = value
                        elif key == "type":
                            data["type"] = value
                        elif key == "created_at":
                            data["created_at"] = value
                        elif key == "updated_at":
                            data["updated_at"] = value

        return data

    def _extract_session_data(self, entity_id: str, file_path: Path) -> dict[str, Any]:
        """Extract session data from JSON file.

        Args:
            entity_id: Session ID.
            file_path: Path to session file.

        Returns:
            Session data dict.
        """
        content = file_path.read_text()
        session_data = json.loads(content)

        data: dict[str, Any] = {"session_id": entity_id}

        if "state" in session_data:
            data["state"] = session_data["state"]
        if "phase" in session_data:
            data["phase"] = session_data["phase"]

        meta = session_data.get("meta", {})
        if "createdAt" in meta:
            data["created_at"] = meta["createdAt"]
        if "lastActive" in meta:
            data["last_active"] = meta["lastActive"]

        return data

    def _extract_qa_data(self, entity_id: str, file_path: Path) -> dict[str, Any]:
        """Extract QA data from markdown file.

        Args:
            entity_id: QA ID.
            file_path: Path to QA file.

        Returns:
            QA data dict.
        """
        content = file_path.read_text()
        data: dict[str, Any] = {"qa_id": entity_id}

        # Parse frontmatter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                for line in frontmatter.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip()
                        value = value.strip().strip("'\"")
                        if key == "id":
                            data["qa_id"] = value
                        elif key == "task_id":
                            data["task_id"] = value
                        elif key == "round":
                            try:
                                data["round"] = int(value)
                            except ValueError:
                                data["round"] = value
                        elif key == "created_at":
                            data["created_at"] = value
                        elif key == "updated_at":
                            data["updated_at"] = value

        return data
