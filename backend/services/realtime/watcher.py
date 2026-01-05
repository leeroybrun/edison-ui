"""File watcher for realtime updates (T051).

Watches Edison project directories and emits change events
for tasks, sessions, and QA files.
"""

from __future__ import annotations

import asyncio
import os
import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from watchfiles import awatch, Change


def _should_force_polling() -> bool:
    """Check if polling mode should be forced.

    Returns True if WATCHFILES_FORCE_POLLING env var is set to a truthy value.
    This is useful for CI environments or containers where native FSEvents
    may not work properly.
    """
    val = os.environ.get("WATCHFILES_FORCE_POLLING", "").lower()
    return val in ("1", "true", "yes")


class EntityType(Enum):
    """Entity types that can be watched."""

    TASK = "task"
    SESSION = "session"
    QA = "qa"


class ChangeType(Enum):
    """Types of changes that can occur."""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass
class ChangeEvent:
    """Represents a file change event."""

    entity_type: EntityType
    entity_id: str
    change_type: ChangeType
    path: str


def detect_entity_type(file_path: Path, project_path: Path) -> EntityType | None:
    """Detect the entity type from a file path.

    Args:
        file_path: Path to the changed file.
        project_path: Path to the project root.

    Returns:
        EntityType if detected, None otherwise.
    """
    try:
        relative = file_path.relative_to(project_path / ".project")
    except ValueError:
        return None

    parts = relative.parts
    if not parts:
        return None

    if parts[0] == "tasks":
        return EntityType.TASK
    elif parts[0] == "sessions":
        return EntityType.SESSION
    elif parts[0] == "qa":
        return EntityType.QA

    return None


def extract_entity_id(file_path: Path, entity_type: str) -> str:
    """Extract entity ID from a file path.

    Args:
        file_path: Path to the file.
        entity_type: Type of entity (task, session, qa).

    Returns:
        The entity ID.
    """
    if entity_type == "task":
        # Task ID is the filename without extension
        return file_path.stem
    elif entity_type == "session":
        # Session ID is the parent directory name (session-XXX)
        return file_path.parent.name
    elif entity_type == "qa":
        # QA ID is the filename without extension
        return file_path.stem
    return file_path.stem


def _watchfiles_change_to_change_type(change: Change, file_path: Path) -> ChangeType:
    """Convert watchfiles Change to ChangeType.

    Note: On macOS, FSEvents may report modifications as 'added' for
    pre-existing files. We detect this by checking if the file exists
    for 'added' events - if it exists, it's a modification.
    """
    if change == Change.deleted:
        return ChangeType.DELETED
    elif change == Change.modified:
        return ChangeType.MODIFIED
    elif change == Change.added:
        # On macOS, modifications are sometimes reported as 'added'
        # If the file exists and is not empty, it's likely a modification
        # of a pre-existing file rather than a true creation
        # However, we can't reliably distinguish, so treat as CREATED
        return ChangeType.CREATED
    return ChangeType.MODIFIED


class FileWatcher:
    """Watches Edison project directories for file changes."""

    def __init__(
        self,
        project_path: str,
        coalesce_ms: int = 100,
    ) -> None:
        """Initialize the file watcher.

        Args:
            project_path: Path to the Edison project.
            coalesce_ms: Milliseconds to wait before emitting coalesced events.
        """
        self.project_path = Path(project_path)
        self.coalesce_ms = coalesce_ms
        self._is_running = False
        self._change_handlers: list[
            Callable[[ChangeEvent], Coroutine[Any, Any, None]]
        ] = []
        self._watch_task: asyncio.Task[None] | None = None
        self._pending_changes: dict[str, tuple[ChangeEvent, float]] = {}
        self._coalesce_task: asyncio.Task[None] | None = None
        self._stop_event: asyncio.Event | None = None
        self._known_files: set[str] = set()  # Track files known at start

    @property
    def is_running(self) -> bool:
        """Check if the watcher is running."""
        return self._is_running

    def get_watched_directories(self) -> list[Path]:
        """Get the directories being watched."""
        project_dir = self.project_path / ".project"
        return [
            project_dir / "tasks",
            project_dir / "sessions",
            project_dir / "qa",
        ]

    def on_change(
        self, handler: Callable[[ChangeEvent], Coroutine[Any, Any, None]]
    ) -> None:
        """Register a change handler.

        Args:
            handler: Async function to call when changes occur.
        """
        self._change_handlers.append(handler)

    async def _emit_event(self, event: ChangeEvent) -> None:
        """Emit an event to all handlers."""
        for handler in self._change_handlers:
            try:
                await handler(event)
            except Exception:
                pass  # Don't let handler errors stop the watcher

    async def _coalesce_loop(self) -> None:
        """Process pending changes after coalesce delay."""
        while self._is_running:
            await asyncio.sleep(0.01)  # Check every 10ms

            now = time.time()
            coalesce_seconds = self.coalesce_ms / 1000.0
            to_emit: list[ChangeEvent] = []

            # Find events that have waited long enough
            paths_to_remove = []
            for path, (event, timestamp) in self._pending_changes.items():
                if now - timestamp >= coalesce_seconds:
                    to_emit.append(event)
                    paths_to_remove.append(path)

            # Remove emitted events
            for path in paths_to_remove:
                del self._pending_changes[path]

            # Emit events
            for event in to_emit:
                await self._emit_event(event)

    async def _watch_loop(self) -> None:
        """Main watch loop using watchfiles."""
        watched_dirs = self.get_watched_directories()
        existing_dirs = [d for d in watched_dirs if d.exists()]

        if not existing_dirs:
            return

        # Use the stop event for graceful shutdown
        # Use short debounce for faster detection
        # force_polling=True for CI/containers where native FSEvents may not work
        force_polling = _should_force_polling()
        async for changes in awatch(
            *existing_dirs,
            stop_event=self._stop_event,
            debounce=50,  # 50ms debounce for faster detection
            force_polling=force_polling,
        ):
            if not self._is_running:
                break

            for change, path_str in changes:
                path = Path(path_str)
                file_exists = path.exists()

                # For deletions, we need to check known files since file doesn't exist
                if change == Change.deleted or not file_exists:
                    # Try to find the resolved path in known files
                    resolved_path = path_str
                    for known in self._known_files:
                        if known.endswith(str(path.name)):
                            resolved_path = known
                            break
                else:
                    resolved_path = str(path.resolve())

                # Skip directories
                if file_exists and path.is_dir():
                    continue

                # Detect entity type
                entity_type = detect_entity_type(path, self.project_path)
                if entity_type is None:
                    continue

                # Extract entity ID
                entity_id = extract_entity_id(path, entity_type.value)

                # Determine change type - on macOS FSEvents reports modifications as 'added'
                # so we check if the file was known before starting
                if change == Change.deleted:
                    change_type = ChangeType.DELETED
                    # Remove from known files
                    self._known_files.discard(resolved_path)
                elif not file_exists:
                    # File doesn't exist but wasn't reported as deleted - treat as deletion
                    change_type = ChangeType.DELETED
                    self._known_files.discard(resolved_path)
                elif resolved_path in self._known_files:
                    # File existed before, so this is a modification
                    change_type = ChangeType.MODIFIED
                else:
                    # New file
                    change_type = ChangeType.CREATED
                    self._known_files.add(resolved_path)

                event = ChangeEvent(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    change_type=change_type,
                    path=str(path),
                )

                # Add to pending changes (coalescing)
                self._pending_changes[path_str] = (event, time.time())

    def _scan_existing_files(self) -> set[str]:
        """Scan for existing files in watched directories."""
        known = set()
        for watch_dir in self.get_watched_directories():
            if watch_dir.exists():
                for f in watch_dir.rglob("*"):
                    if f.is_file():
                        known.add(str(f.resolve()))
        return known

    async def start(self) -> None:
        """Start watching for file changes."""
        if self._is_running:
            return

        self._is_running = True
        self._pending_changes = {}
        self._stop_event = asyncio.Event()

        # Scan for existing files before starting
        self._known_files = self._scan_existing_files()

        # Start coalesce loop
        self._coalesce_task = asyncio.create_task(self._coalesce_loop())

        # Start watch loop
        self._watch_task = asyncio.create_task(self._watch_loop())

    async def stop(self) -> None:
        """Stop watching for file changes."""
        if not self._is_running:
            return

        self._is_running = False

        # Signal the watcher to stop
        if self._stop_event:
            self._stop_event.set()

        # Cancel tasks
        if self._coalesce_task:
            self._coalesce_task.cancel()
            try:
                await self._coalesce_task
            except asyncio.CancelledError:
                pass
            self._coalesce_task = None

        if self._watch_task:
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass
            self._watch_task = None

        self._pending_changes = {}
        self._stop_event = None
