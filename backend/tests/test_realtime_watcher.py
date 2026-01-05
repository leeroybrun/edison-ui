"""Tests for realtime file watcher service (T051).

RED Phase: These tests MUST fail initially as the services don't exist yet.
Tests the file watcher, differ, and publisher components for the realtime pipeline.

Uses real filesystem with tmp_path fixture - NO MOCKS for filesystem operations.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from services.realtime.watcher import ChangeEvent


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def edison_project(tmp_path: Path) -> Path:
    """Create a minimal Edison project structure for testing."""
    project = tmp_path / "test-project"
    project.mkdir()
    (project / ".edison").mkdir()

    project_dir = project / ".project"
    project_dir.mkdir()

    # Create task directories
    tasks_dir = project_dir / "tasks"
    tasks_dir.mkdir()
    for state in ["todo", "wip", "blocked", "done", "validated"]:
        (tasks_dir / state).mkdir()

    # Create session directories
    sessions_dir = project_dir / "sessions"
    sessions_dir.mkdir()
    for state in ["draft", "active", "blocked", "paused", "done", "validated"]:
        (sessions_dir / state).mkdir()

    # Create QA directories
    qa_dir = project_dir / "qa"
    qa_dir.mkdir()
    for state in ["waiting", "todo", "wip", "done", "validated"]:
        (qa_dir / state).mkdir()

    return project


@pytest.fixture
def task_content() -> str:
    """Return sample task markdown content."""
    return """---
id: T001
title: Test Task
type: implementation
created_at: '2025-12-27T10:00:00Z'
updated_at: '2025-12-27T10:00:00Z'
---
# Task T001
Test task content.
"""


@pytest.fixture
def session_content() -> dict[str, object]:
    """Return sample session JSON content."""
    return {
        "id": "session-001",
        "state": "active",
        "phase": "implementation",
        "meta": {
            "sessionId": "session-001",
            "createdAt": "2025-12-27T10:00:00Z",
            "lastActive": "2025-12-27T10:00:00Z",
        },
        "tasks": {},
    }


@pytest.fixture
def qa_content() -> str:
    """Return sample QA markdown content."""
    return """---
id: T001-qa
task_id: T001
round: 1
validators:
  - validator-a
created_at: '2025-12-27T10:00:00Z'
updated_at: '2025-12-27T10:00:00Z'
---
# QA for T001
"""


# =============================================================================
# EntityType Tests
# =============================================================================


class TestEntityType:
    """Tests for entity type detection."""

    def test_entity_type_enum_values(self) -> None:
        """Should define task, session, and qa entity types."""
        from services.realtime.watcher import EntityType

        assert EntityType.TASK.value == "task"
        assert EntityType.SESSION.value == "session"
        assert EntityType.QA.value == "qa"

    def test_detect_entity_type_for_task(self, edison_project: Path) -> None:
        """Should detect task entity from task file path."""
        from services.realtime.watcher import detect_entity_type

        task_path = edison_project / ".project" / "tasks" / "todo" / "T001.md"
        entity_type = detect_entity_type(task_path, edison_project)

        assert entity_type is not None
        assert entity_type.value == "task"

    def test_detect_entity_type_for_session(self, edison_project: Path) -> None:
        """Should detect session entity from session.json path."""
        from services.realtime.watcher import detect_entity_type

        session_path = (
            edison_project
            / ".project"
            / "sessions"
            / "active"
            / "session-001"
            / "session.json"
        )
        entity_type = detect_entity_type(session_path, edison_project)

        assert entity_type is not None
        assert entity_type.value == "session"

    def test_detect_entity_type_for_qa(self, edison_project: Path) -> None:
        """Should detect QA entity from QA file path."""
        from services.realtime.watcher import detect_entity_type

        qa_path = edison_project / ".project" / "qa" / "wip" / "T001-qa.md"
        entity_type = detect_entity_type(qa_path, edison_project)

        assert entity_type is not None
        assert entity_type.value == "qa"

    def test_detect_entity_type_returns_none_for_unknown(
        self, edison_project: Path
    ) -> None:
        """Should return None for paths outside watched directories."""
        from services.realtime.watcher import detect_entity_type

        unknown_path = edison_project / "some" / "other" / "file.txt"
        entity_type = detect_entity_type(unknown_path, edison_project)

        assert entity_type is None


# =============================================================================
# ChangeEvent Tests
# =============================================================================


class TestChangeEvent:
    """Tests for change event data class."""

    def test_change_event_fields(self) -> None:
        """Should have required fields: entity_type, entity_id, change_type, path."""
        from services.realtime.watcher import ChangeEvent, ChangeType, EntityType

        event = ChangeEvent(
            entity_type=EntityType.TASK,
            entity_id="T001",
            change_type=ChangeType.CREATED,
            path="/path/to/task.md",
        )

        assert event.entity_type == EntityType.TASK
        assert event.entity_id == "T001"
        assert event.change_type == ChangeType.CREATED
        assert event.path == "/path/to/task.md"

    def test_change_type_enum_values(self) -> None:
        """Should define created, modified, deleted change types."""
        from services.realtime.watcher import ChangeType

        assert ChangeType.CREATED.value == "created"
        assert ChangeType.MODIFIED.value == "modified"
        assert ChangeType.DELETED.value == "deleted"


# =============================================================================
# FileWatcher Tests
# =============================================================================


class TestFileWatcher:
    """Tests for the file watcher service."""

    def test_watcher_initialization(self, edison_project: Path) -> None:
        """Should initialize watcher with project path."""
        from services.realtime.watcher import FileWatcher

        watcher = FileWatcher(project_path=str(edison_project))

        assert watcher.project_path == edison_project
        assert watcher.is_running is False

    def test_watcher_watches_correct_directories(self, edison_project: Path) -> None:
        """Should watch .project/tasks, .project/sessions, .project/qa."""
        from services.realtime.watcher import FileWatcher

        watcher = FileWatcher(project_path=str(edison_project))
        watched_dirs = watcher.get_watched_directories()

        assert edison_project / ".project" / "tasks" in watched_dirs
        assert edison_project / ".project" / "sessions" in watched_dirs
        assert edison_project / ".project" / "qa" in watched_dirs

    @pytest.mark.asyncio
    async def test_watcher_detects_file_creation(
        self, edison_project: Path, task_content: str
    ) -> None:
        """Should detect when a new task file is created."""
        from services.realtime.watcher import ChangeType, EntityType, FileWatcher

        watcher = FileWatcher(
            project_path=str(edison_project),
            coalesce_ms=50,  # Short coalesce for faster tests
        )

        events: list[ChangeEvent] = []

        async def capture_event(event: ChangeEvent) -> None:
            events.append(event)

        watcher.on_change(capture_event)

        # Start watcher
        await watcher.start()

        try:
            # Give watcher time to initialize
            await asyncio.sleep(0.3)

            # Create a new task file
            task_file = edison_project / ".project" / "tasks" / "todo" / "T001.md"
            task_file.write_text(task_content)

            # Wait for FSEvents/polling to deliver the event
            # Polling mode uses ~300ms intervals, so 1s gives enough margin
            await asyncio.sleep(1.0)

        finally:
            await watcher.stop()

        # Verify event captured
        assert len(events) >= 1
        event = events[0]
        assert event.entity_type == EntityType.TASK
        assert event.entity_id == "T001"
        assert event.change_type == ChangeType.CREATED

    @pytest.mark.asyncio
    async def test_watcher_detects_file_modification(
        self, edison_project: Path, task_content: str
    ) -> None:
        """Should detect when an existing task file is modified."""
        from services.realtime.watcher import ChangeType, EntityType, FileWatcher

        # Pre-create the task file BEFORE starting the watcher
        # This ensures it's in _known_files when the watcher starts
        task_file = edison_project / ".project" / "tasks" / "wip" / "T002.md"
        task_file.write_text(task_content.replace("T001", "T002"))

        watcher = FileWatcher(
            project_path=str(edison_project),
            coalesce_ms=50,
        )

        events: list[ChangeEvent] = []

        async def capture_event(event: ChangeEvent) -> None:
            events.append(event)

        watcher.on_change(capture_event)

        await watcher.start()

        try:
            # Wait for watcher to complete initial poll cycle
            # In polling mode, awatch needs time to establish baseline state
            # before it can detect changes. Use generous wait for CI stability.
            await asyncio.sleep(1.5)

            # Modify the task file - ensure mtime changes
            await asyncio.sleep(0.1)  # Small gap to ensure mtime differs
            task_file.write_text(task_content.replace("T001", "T002") + "\nUpdated!")

            # Wait for FSEvents/polling to deliver the event with retry
            # Polling mode can be slow in some CI environments
            for _ in range(8):  # Retry up to 8 times (4 seconds total)
                await asyncio.sleep(0.5)
                if events:
                    break

        finally:
            await watcher.stop()

        # Should detect modification
        assert len(events) >= 1
        # Find modification event (may have multiple events)
        mod_events = [e for e in events if e.change_type == ChangeType.MODIFIED]
        assert len(mod_events) >= 1
        assert mod_events[0].entity_type == EntityType.TASK
        assert mod_events[0].entity_id == "T002"

    @pytest.mark.asyncio
    async def test_watcher_detects_file_deletion(
        self, edison_project: Path, task_content: str
    ) -> None:
        """Should detect when a task file is deleted."""
        from services.realtime.watcher import ChangeType, EntityType, FileWatcher

        # Pre-create the task file
        task_file = edison_project / ".project" / "tasks" / "done" / "T003.md"
        task_file.write_text(task_content.replace("T001", "T003"))

        watcher = FileWatcher(
            project_path=str(edison_project),
            coalesce_ms=50,
        )

        events: list[ChangeEvent] = []

        async def capture_event(event: ChangeEvent) -> None:
            events.append(event)

        watcher.on_change(capture_event)

        await watcher.start()

        try:
            await asyncio.sleep(0.3)

            # Delete the task file
            task_file.unlink()

            # Wait for FSEvents/polling to deliver the event
            # Polling mode uses ~300ms intervals, so 1s gives enough margin
            await asyncio.sleep(1.0)

        finally:
            await watcher.stop()

        # Should detect deletion
        assert len(events) >= 1
        del_events = [e for e in events if e.change_type == ChangeType.DELETED]
        assert len(del_events) >= 1
        assert del_events[0].entity_type == EntityType.TASK
        assert del_events[0].entity_id == "T003"

    @pytest.mark.asyncio
    async def test_watcher_detects_session_changes(
        self, edison_project: Path, session_content: dict[str, object]
    ) -> None:
        """Should detect session.json file changes."""
        from services.realtime.watcher import EntityType, FileWatcher

        watcher = FileWatcher(
            project_path=str(edison_project),
            coalesce_ms=50,
        )

        events: list[ChangeEvent] = []

        async def capture_event(event: ChangeEvent) -> None:
            events.append(event)

        watcher.on_change(capture_event)

        await watcher.start()

        try:
            await asyncio.sleep(0.3)

            # Create session directory and file
            session_dir = (
                edison_project / ".project" / "sessions" / "active" / "session-001"
            )
            session_dir.mkdir(parents=True, exist_ok=True)
            session_file = session_dir / "session.json"
            session_file.write_text(json.dumps(session_content))

            # Wait for FSEvents/polling to deliver the event
            # Polling mode uses ~300ms intervals, so 1s gives enough margin
            await asyncio.sleep(1.0)

        finally:
            await watcher.stop()

        # Should detect session creation
        assert len(events) >= 1
        session_events = [e for e in events if e.entity_type == EntityType.SESSION]
        assert len(session_events) >= 1
        assert session_events[0].entity_id == "session-001"

    @pytest.mark.asyncio
    async def test_watcher_detects_qa_changes(
        self, edison_project: Path, qa_content: str
    ) -> None:
        """Should detect QA file changes."""
        from services.realtime.watcher import EntityType, FileWatcher

        watcher = FileWatcher(
            project_path=str(edison_project),
            coalesce_ms=50,
        )

        events: list[ChangeEvent] = []

        async def capture_event(event: ChangeEvent) -> None:
            events.append(event)

        watcher.on_change(capture_event)

        await watcher.start()

        try:
            await asyncio.sleep(0.3)

            # Create QA file
            qa_file = edison_project / ".project" / "qa" / "wip" / "T001-qa.md"
            qa_file.write_text(qa_content)

            # Wait for FSEvents/polling to deliver the event
            # Polling mode uses ~300ms intervals, so 1s gives enough margin
            await asyncio.sleep(1.0)

        finally:
            await watcher.stop()

        # Should detect QA creation
        assert len(events) >= 1
        qa_events = [e for e in events if e.entity_type == EntityType.QA]
        assert len(qa_events) >= 1
        assert qa_events[0].entity_id == "T001-qa"


# =============================================================================
# Change Coalescing Tests
# =============================================================================


class TestChangeCoalescing:
    """Tests for debouncing/coalescing rapid changes."""

    @pytest.mark.asyncio
    async def test_coalesces_rapid_changes(
        self, edison_project: Path, task_content: str
    ) -> None:
        """Should coalesce multiple rapid changes into a single event."""
        from services.realtime.watcher import FileWatcher

        watcher = FileWatcher(
            project_path=str(edison_project),
            coalesce_ms=200,  # 200ms coalesce window
        )

        events: list[ChangeEvent] = []

        async def capture_event(event: ChangeEvent) -> None:
            events.append(event)

        watcher.on_change(capture_event)

        await watcher.start()

        try:
            await asyncio.sleep(0.3)

            # Create and rapidly modify the same file
            task_file = edison_project / ".project" / "tasks" / "todo" / "T010.md"
            task_file.write_text(task_content.replace("T001", "T010"))
            await asyncio.sleep(0.1)
            task_file.write_text(task_content.replace("T001", "T010") + "\nLine 2")
            await asyncio.sleep(0.1)
            task_file.write_text(task_content.replace("T001", "T010") + "\nLine 3")

            # Wait for FSEvents/polling + coalesce window to pass
            # Polling mode uses ~300ms intervals, so 1.2s gives enough margin
            await asyncio.sleep(1.2)

        finally:
            await watcher.stop()

        # Should have coalesced into fewer events (ideally 1-2)
        assert len(events) <= 2

    @pytest.mark.asyncio
    async def test_does_not_coalesce_different_files(
        self, edison_project: Path, task_content: str
    ) -> None:
        """Should not coalesce changes to different files."""
        from services.realtime.watcher import FileWatcher

        watcher = FileWatcher(
            project_path=str(edison_project),
            coalesce_ms=100,
        )

        events: list[ChangeEvent] = []

        async def capture_event(event: ChangeEvent) -> None:
            events.append(event)

        watcher.on_change(capture_event)

        await watcher.start()

        try:
            await asyncio.sleep(0.3)

            # Create two different files
            task1 = edison_project / ".project" / "tasks" / "todo" / "T011.md"
            task2 = edison_project / ".project" / "tasks" / "todo" / "T012.md"
            task1.write_text(task_content.replace("T001", "T011"))
            task2.write_text(task_content.replace("T001", "T012"))

            # Wait for FSEvents/polling to deliver the events
            # Polling mode uses ~300ms intervals, so 1s gives enough margin
            await asyncio.sleep(1.0)

        finally:
            await watcher.stop()

        # Should have events for both files
        entity_ids = {e.entity_id for e in events}
        assert "T011" in entity_ids
        assert "T012" in entity_ids


# =============================================================================
# Differ Tests
# =============================================================================


class TestDiffer:
    """Tests for the diff service."""

    def test_differ_initialization(self, edison_project: Path) -> None:
        """Should initialize differ with project path."""
        from services.realtime.differ import Differ

        differ = Differ(project_path=str(edison_project))
        assert differ.project_path == edison_project

    def test_differ_detects_task_upsert(
        self, edison_project: Path, task_content: str
    ) -> None:
        """Should detect task upsert when file exists."""
        from services.realtime.differ import Differ
        from services.realtime.watcher import ChangeEvent, ChangeType, EntityType

        task_file = edison_project / ".project" / "tasks" / "todo" / "T001.md"
        task_file.write_text(task_content)

        differ = Differ(project_path=str(edison_project))

        event = ChangeEvent(
            entity_type=EntityType.TASK,
            entity_id="T001",
            change_type=ChangeType.CREATED,
            path=str(task_file),
        )

        result = differ.process_change(event)

        assert result is not None
        assert result.entity_type == EntityType.TASK
        assert result.entity_id == "T001"
        assert result.data is not None
        assert result.data["task_id"] == "T001"

    def test_differ_detects_delete(self, edison_project: Path) -> None:
        """Should detect delete when file doesn't exist."""
        from services.realtime.differ import Differ
        from services.realtime.watcher import ChangeEvent, ChangeType, EntityType

        differ = Differ(project_path=str(edison_project))

        # File doesn't exist (deleted)
        event = ChangeEvent(
            entity_type=EntityType.TASK,
            entity_id="T099",
            change_type=ChangeType.DELETED,
            path=str(edison_project / ".project" / "tasks" / "todo" / "T099.md"),
        )

        result = differ.process_change(event)

        assert result is not None
        assert result.change_type == ChangeType.DELETED
        assert result.data is None

    def test_differ_returns_session_data(
        self, edison_project: Path, session_content: dict[str, object]
    ) -> None:
        """Should return session data for session changes."""
        from services.realtime.differ import Differ
        from services.realtime.watcher import ChangeEvent, ChangeType, EntityType

        session_dir = (
            edison_project / ".project" / "sessions" / "active" / "session-001"
        )
        session_dir.mkdir(parents=True, exist_ok=True)
        session_file = session_dir / "session.json"
        session_file.write_text(json.dumps(session_content))

        differ = Differ(project_path=str(edison_project))

        event = ChangeEvent(
            entity_type=EntityType.SESSION,
            entity_id="session-001",
            change_type=ChangeType.CREATED,
            path=str(session_file),
        )

        result = differ.process_change(event)

        assert result is not None
        assert result.entity_type == EntityType.SESSION
        assert result.data is not None
        assert result.data["session_id"] == "session-001"


# =============================================================================
# DiffResult Tests
# =============================================================================


class TestDiffResult:
    """Tests for DiffResult data class."""

    def test_diff_result_fields(self) -> None:
        """Should have entity_type, entity_id, change_type, and optional data."""
        from services.realtime.differ import DiffResult
        from services.realtime.watcher import ChangeType, EntityType

        result = DiffResult(
            entity_type=EntityType.TASK,
            entity_id="T001",
            change_type=ChangeType.MODIFIED,
            data={"task_id": "T001", "title": "Test"},
        )

        assert result.entity_type == EntityType.TASK
        assert result.entity_id == "T001"
        assert result.change_type == ChangeType.MODIFIED
        assert result.data is not None
        assert result.data["title"] == "Test"

    def test_diff_result_delete_has_no_data(self) -> None:
        """Deleted entities should have no data."""
        from services.realtime.differ import DiffResult
        from services.realtime.watcher import ChangeType, EntityType

        result = DiffResult(
            entity_type=EntityType.TASK,
            entity_id="T099",
            change_type=ChangeType.DELETED,
            data=None,
        )

        assert result.data is None


# =============================================================================
# Publisher Tests
# =============================================================================


class TestPublisher:
    """Tests for the publisher interface."""

    def test_publisher_interface_exists(self) -> None:
        """Should define an abstract Publisher interface."""
        from services.realtime.publisher import Publisher

        # Should not be instantiable directly
        with pytest.raises(TypeError):
            Publisher()  # type: ignore[abstract]

    def test_memory_publisher_exists(self) -> None:
        """Should have a MemoryPublisher for testing."""
        from services.realtime.publisher import MemoryPublisher

        publisher = MemoryPublisher(max_queue_size=100)
        assert publisher is not None

    @pytest.mark.asyncio
    async def test_memory_publisher_publishes_events(self) -> None:
        """Should publish events to internal queue."""
        from services.realtime.differ import DiffResult
        from services.realtime.publisher import MemoryPublisher
        from services.realtime.watcher import ChangeType, EntityType

        publisher = MemoryPublisher(max_queue_size=100)

        result = DiffResult(
            entity_type=EntityType.TASK,
            entity_id="T001",
            change_type=ChangeType.CREATED,
            data={"task_id": "T001"},
        )

        await publisher.publish(result)

        events = publisher.get_events()
        assert len(events) == 1
        assert events[0].entity_id == "T001"

    @pytest.mark.asyncio
    async def test_memory_publisher_respects_max_queue_size(self) -> None:
        """Should drop oldest events when queue is full."""
        from services.realtime.differ import DiffResult
        from services.realtime.publisher import MemoryPublisher
        from services.realtime.watcher import ChangeType, EntityType

        publisher = MemoryPublisher(max_queue_size=3)

        # Publish 5 events (exceeds max_queue_size of 3)
        for i in range(5):
            result = DiffResult(
                entity_type=EntityType.TASK,
                entity_id=f"T00{i}",
                change_type=ChangeType.CREATED,
                data={"task_id": f"T00{i}"},
            )
            await publisher.publish(result)

        events = publisher.get_events()
        # Should only keep the most recent 3
        assert len(events) == 3
        # Should have T002, T003, T004 (oldest T000, T001 dropped)
        entity_ids = [e.entity_id for e in events]
        assert "T002" in entity_ids
        assert "T003" in entity_ids
        assert "T004" in entity_ids

    @pytest.mark.asyncio
    async def test_publisher_clear_events(self) -> None:
        """Should clear all events."""
        from services.realtime.differ import DiffResult
        from services.realtime.publisher import MemoryPublisher
        from services.realtime.watcher import ChangeType, EntityType

        publisher = MemoryPublisher(max_queue_size=100)

        result = DiffResult(
            entity_type=EntityType.TASK,
            entity_id="T001",
            change_type=ChangeType.CREATED,
            data={"task_id": "T001"},
        )

        await publisher.publish(result)
        assert len(publisher.get_events()) == 1

        publisher.clear()
        assert len(publisher.get_events()) == 0


# =============================================================================
# Integration Tests
# =============================================================================


class TestRealtimePipeline:
    """Integration tests for the full watcher -> differ -> publisher pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, edison_project: Path, task_content: str) -> None:
        """Should detect changes, compute diffs, and publish events."""
        from services.realtime.differ import Differ
        from services.realtime.publisher import MemoryPublisher
        from services.realtime.watcher import EntityType, FileWatcher

        publisher = MemoryPublisher(max_queue_size=100)
        differ = Differ(project_path=str(edison_project))
        watcher = FileWatcher(
            project_path=str(edison_project),
            coalesce_ms=50,
        )

        async def process_change(event: ChangeEvent) -> None:
            result = differ.process_change(event)
            if result:
                await publisher.publish(result)

        watcher.on_change(process_change)

        await watcher.start()

        try:
            await asyncio.sleep(0.3)

            # Create a task
            task_file = edison_project / ".project" / "tasks" / "todo" / "T100.md"
            task_file.write_text(task_content.replace("T001", "T100"))

            # Wait for FSEvents/polling to deliver the event
            # Polling mode uses ~300ms intervals, so 1s gives enough margin
            await asyncio.sleep(1.0)

        finally:
            await watcher.stop()

        # Verify full pipeline worked
        events = publisher.get_events()
        assert len(events) >= 1

        # Find the task event
        task_events = [e for e in events if e.entity_type == EntityType.TASK]
        assert len(task_events) >= 1
        assert task_events[0].entity_id == "T100"
        assert task_events[0].data is not None
        assert task_events[0].data["task_id"] == "T100"

    @pytest.mark.asyncio
    async def test_pipeline_handles_rapid_updates(
        self, edison_project: Path, task_content: str
    ) -> None:
        """Pipeline should handle rapid file updates gracefully."""
        from services.realtime.differ import Differ
        from services.realtime.publisher import MemoryPublisher
        from services.realtime.watcher import FileWatcher

        publisher = MemoryPublisher(max_queue_size=100)
        differ = Differ(project_path=str(edison_project))
        watcher = FileWatcher(
            project_path=str(edison_project),
            coalesce_ms=100,
        )

        async def process_change(event: ChangeEvent) -> None:
            result = differ.process_change(event)
            if result:
                await publisher.publish(result)

        watcher.on_change(process_change)

        await watcher.start()

        try:
            await asyncio.sleep(0.3)

            task_file = edison_project / ".project" / "tasks" / "wip" / "T200.md"

            # Rapid updates
            for i in range(10):
                content = task_content.replace("T001", "T200") + f"\nUpdate {i}"
                task_file.write_text(content)
                await asyncio.sleep(0.05)  # 50ms between updates

            # Wait for FSEvents/polling + coalescing
            # Polling mode uses ~300ms intervals, so 1.2s gives enough margin
            await asyncio.sleep(1.2)

        finally:
            await watcher.stop()

        # Should have processed events without errors
        events = publisher.get_events()
        # Due to coalescing, should have fewer than 10 events
        assert len(events) < 10
        assert len(events) >= 1


# =============================================================================
# Entity ID Extraction Tests
# =============================================================================


class TestEntityIdExtraction:
    """Tests for extracting entity IDs from file paths."""

    def test_extract_task_id_from_path(self, edison_project: Path) -> None:
        """Should extract task ID from task file path."""
        from services.realtime.watcher import extract_entity_id

        path = edison_project / ".project" / "tasks" / "todo" / "T001.md"
        entity_id = extract_entity_id(path, "task")

        assert entity_id == "T001"

    def test_extract_session_id_from_path(self, edison_project: Path) -> None:
        """Should extract session ID from session directory path."""
        from services.realtime.watcher import extract_entity_id

        path = (
            edison_project
            / ".project"
            / "sessions"
            / "active"
            / "session-001"
            / "session.json"
        )
        entity_id = extract_entity_id(path, "session")

        assert entity_id == "session-001"

    def test_extract_qa_id_from_path(self, edison_project: Path) -> None:
        """Should extract QA ID from QA file path."""
        from services.realtime.watcher import extract_entity_id

        path = edison_project / ".project" / "qa" / "wip" / "T001-qa.md"
        entity_id = extract_entity_id(path, "qa")

        assert entity_id == "T001-qa"


# =============================================================================
# Watcher Start/Stop Tests
# =============================================================================


class TestWatcherLifecycle:
    """Tests for watcher lifecycle management."""

    @pytest.mark.asyncio
    async def test_watcher_can_start_and_stop(self, edison_project: Path) -> None:
        """Should start and stop cleanly."""
        from services.realtime.watcher import FileWatcher

        watcher = FileWatcher(project_path=str(edison_project))

        await watcher.start()
        assert watcher.is_running is True

        await watcher.stop()
        assert watcher.is_running is False

    @pytest.mark.asyncio
    async def test_watcher_idempotent_start(self, edison_project: Path) -> None:
        """Starting twice should be safe."""
        from services.realtime.watcher import FileWatcher

        watcher = FileWatcher(project_path=str(edison_project))

        await watcher.start()
        await watcher.start()  # Second start should be no-op
        assert watcher.is_running is True

        await watcher.stop()

    @pytest.mark.asyncio
    async def test_watcher_idempotent_stop(self, edison_project: Path) -> None:
        """Stopping twice should be safe."""
        from services.realtime.watcher import FileWatcher

        watcher = FileWatcher(project_path=str(edison_project))

        await watcher.start()
        await watcher.stop()
        await watcher.stop()  # Second stop should be no-op
        assert watcher.is_running is False


# =============================================================================
# Settings Tests
# =============================================================================


class TestRealtimeSettings:
    """Tests for realtime configuration settings."""

    def test_realtime_enabled_setting(self) -> None:
        """Should have realtime_enabled setting with default True."""
        from core.settings import Settings

        settings = Settings()
        assert hasattr(settings, "realtime_enabled")
        assert settings.realtime_enabled is True

    def test_realtime_coalesce_ms_setting(self) -> None:
        """Should have realtime_coalesce_ms setting with default 100."""
        from core.settings import Settings

        settings = Settings()
        assert hasattr(settings, "realtime_coalesce_ms")
        assert settings.realtime_coalesce_ms == 100

    def test_realtime_max_queue_size_setting(self) -> None:
        """Should have realtime_max_queue_size setting with default 1000."""
        from core.settings import Settings

        settings = Settings()
        assert hasattr(settings, "realtime_max_queue_size")
        assert settings.realtime_max_queue_size == 1000
