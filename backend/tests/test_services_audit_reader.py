"""Tests for AuditReaderService (T078).

Tests audit JSONL reading with filtering and pagination.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


class TestAuditReaderService:
    """Test cases for AuditReaderService."""

    @pytest.fixture
    def project_root(self, tmp_path: Path) -> Path:
        """Create a temporary project root with Edison structure."""
        edison_logs = tmp_path / ".project" / "logs" / "edison"
        edison_logs.mkdir(parents=True)
        return tmp_path

    @pytest.fixture
    def sample_audit_entries(self) -> list[dict]:
        """Sample audit entries matching Edison's format."""
        return [
            {
                "ts": "2026-01-01T10:00:00Z",
                "event": "cli.invocation.start",
                "pid": 1000,
                "invocation_id": "inv-001",
                "session_id": "session-1",
                "task_id": None,
                "project_root": "/project",
                "command": "session create",
            },
            {
                "ts": "2026-01-01T10:00:05Z",
                "event": "cli.invocation.end",
                "pid": 1000,
                "invocation_id": "inv-001",
                "session_id": "session-1",
                "task_id": None,
                "project_root": "/project",
                "command": "session create",
                "exit_code": 0,
                "duration_ms": 5000,
            },
            {
                "ts": "2026-01-01T11:00:00Z",
                "event": "cli.invocation.start",
                "pid": 1001,
                "invocation_id": "inv-002",
                "session_id": "session-1",
                "task_id": "task-1",
                "project_root": "/project",
                "command": "task claim task-1",
            },
            {
                "ts": "2026-01-01T11:00:02Z",
                "event": "cli.invocation.end",
                "pid": 1001,
                "invocation_id": "inv-002",
                "session_id": "session-1",
                "task_id": "task-1",
                "project_root": "/project",
                "command": "task claim task-1",
                "exit_code": 0,
                "duration_ms": 2000,
            },
            {
                "ts": "2026-01-01T12:00:00Z",
                "event": "cli.invocation.start",
                "pid": 1002,
                "invocation_id": "inv-003",
                "session_id": "session-2",
                "task_id": None,
                "project_root": "/project",
                "command": "session create",
            },
        ]

    @pytest.fixture
    def audit_file(
        self, project_root: Path, sample_audit_entries: list[dict]
    ) -> Path:
        """Create a sample audit JSONL file."""
        audit_path = project_root / ".project" / "logs" / "edison" / "audit.jsonl"
        with open(audit_path, "w") as f:
            for entry in sample_audit_entries:
                f.write(json.dumps(entry) + "\n")
        return audit_path

    def test_read_all_audit_entries(
        self, project_root: Path, audit_file: Path, sample_audit_entries: list[dict]
    ) -> None:
        """Should read all audit entries from JSONL file."""
        from services.audit_reader import AuditReaderService

        service = AuditReaderService(project_root)
        result = service.read_audit_events()

        assert len(result.items) == len(sample_audit_entries)
        assert result.has_more is False

    def test_filter_by_session_id(
        self, project_root: Path, audit_file: Path
    ) -> None:
        """Should filter audit entries by session_id."""
        from services.audit_reader import AuditReaderService

        service = AuditReaderService(project_root)
        result = service.read_audit_events(session_id="session-1")

        # 4 entries for session-1
        assert len(result.items) == 4
        for item in result.items:
            assert item.session_id == "session-1"

    def test_filter_by_invocation_id(
        self, project_root: Path, audit_file: Path
    ) -> None:
        """Should filter audit entries by invocation_id."""
        from services.audit_reader import AuditReaderService

        service = AuditReaderService(project_root)
        result = service.read_audit_events(invocation_id="inv-002")

        # 2 entries for inv-002 (start and end)
        assert len(result.items) == 2
        for item in result.items:
            assert item.invocation_id == "inv-002"

    def test_filter_by_since_timestamp(
        self, project_root: Path, audit_file: Path
    ) -> None:
        """Should filter audit entries since a timestamp."""
        from services.audit_reader import AuditReaderService

        service = AuditReaderService(project_root)
        # Should return entries from 11:00 onwards
        result = service.read_audit_events(since="2026-01-01T10:30:00Z")

        # 3 entries after 10:30
        assert len(result.items) == 3

    def test_limit_results(
        self, project_root: Path, audit_file: Path
    ) -> None:
        """Should respect limit parameter."""
        from services.audit_reader import AuditReaderService

        service = AuditReaderService(project_root)
        result = service.read_audit_events(limit=2)

        assert len(result.items) == 2
        assert result.has_more is True

    def test_empty_log_directory(self, project_root: Path) -> None:
        """Should return empty results if no log files exist."""
        from services.audit_reader import AuditReaderService

        service = AuditReaderService(project_root)
        result = service.read_audit_events()

        assert len(result.items) == 0
        assert result.has_more is False

    def test_redacts_external_paths(
        self, project_root: Path, sample_audit_entries: list[dict]
    ) -> None:
        """Should redact paths outside project root."""
        from services.audit_reader import AuditReaderService

        # Add an entry with external path
        audit_path = project_root / ".project" / "logs" / "edison" / "audit.jsonl"
        entry_with_external = {
            "ts": "2026-01-01T13:00:00Z",
            "event": "cli.invocation.start",
            "pid": 2000,
            "invocation_id": "inv-ext",
            "session_id": None,
            "task_id": None,
            "project_root": "/Users/secret/project",  # External path
            "command": "test",
            "stdout_path": "/Users/secret/logs/out.log",  # External path
        }
        with open(audit_path, "w") as f:
            f.write(json.dumps(entry_with_external) + "\n")

        service = AuditReaderService(project_root)
        result = service.read_audit_events()

        assert len(result.items) == 1
        # project_root should be redacted
        assert result.items[0].project_root == "[REDACTED_PATH]"


class TestActivityConversion:
    """Test converting audit events to activity items."""

    @pytest.fixture
    def project_root(self, tmp_path: Path) -> Path:
        """Create a temporary project root with Edison structure."""
        edison_logs = tmp_path / ".project" / "logs" / "edison"
        edison_logs.mkdir(parents=True)
        return tmp_path

    @pytest.fixture
    def cli_audit_entries(self) -> list[dict]:
        """CLI invocation audit entries for activity conversion."""
        return [
            {
                "ts": "2026-01-01T10:00:00Z",
                "event": "cli.invocation.start",
                "pid": 1000,
                "invocation_id": "inv-001",
                "session_id": "session-1",
                "task_id": None,
                "project_root": "/project",
                "command": "session create",
            },
            {
                "ts": "2026-01-01T10:00:05Z",
                "event": "cli.invocation.end",
                "pid": 1000,
                "invocation_id": "inv-001",
                "session_id": "session-1",
                "task_id": None,
                "project_root": "/project",
                "command": "session create",
                "exit_code": 0,
                "duration_ms": 5000,
            },
        ]

    def test_convert_cli_invocation_to_activity(
        self, project_root: Path, cli_audit_entries: list[dict]
    ) -> None:
        """Should convert CLI invocation pairs into activity items."""
        from services.audit_reader import AuditReaderService

        audit_path = project_root / ".project" / "logs" / "edison" / "audit.jsonl"
        with open(audit_path, "w") as f:
            for entry in cli_audit_entries:
                f.write(json.dumps(entry) + "\n")

        service = AuditReaderService(project_root)
        result = service.read_activity()

        # Should consolidate start/end into one activity
        assert len(result.items) == 1
        activity = result.items[0]
        assert activity.event_type == "session.create"
        assert activity.session_id == "session-1"
        assert activity.invocation_id == "inv-001"

    def test_activity_filters_subprocess_events(
        self, project_root: Path
    ) -> None:
        """Activity view should filter out low-level subprocess events."""
        from services.audit_reader import AuditReaderService

        # Mix of CLI and subprocess events
        entries = [
            {
                "ts": "2026-01-01T10:00:00Z",
                "event": "subprocess.start",
                "pid": 1000,
                "invocation_id": None,
                "session_id": None,
                "task_id": None,
                "project_root": "/project",
                "argv": ["git", "status"],
            },
            {
                "ts": "2026-01-01T10:00:01Z",
                "event": "cli.invocation.end",
                "pid": 1001,
                "invocation_id": "inv-001",
                "session_id": "session-1",
                "task_id": None,
                "project_root": "/project",
                "command": "session create",
                "exit_code": 0,
                "duration_ms": 1000,
            },
        ]

        audit_path = project_root / ".project" / "logs" / "edison" / "audit.jsonl"
        with open(audit_path, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        service = AuditReaderService(project_root)
        result = service.read_activity()

        # Only CLI invocation should show, not subprocess
        assert len(result.items) == 1
        assert result.items[0].event_type == "session.create"


class TestTimestampParsing:
    """Test cases for _parse_timestamp datetime handling."""

    def test_parse_iso_with_z_suffix(self) -> None:
        """Should parse ISO timestamp with Z suffix."""
        from datetime import timezone

        from services.audit_reader import _parse_timestamp

        result = _parse_timestamp("2026-01-01T10:00:00Z")
        assert result is not None
        assert result.tzinfo == timezone.utc
        assert result.year == 2026
        assert result.month == 1
        assert result.hour == 10

    def test_parse_iso_with_offset(self) -> None:
        """Should parse ISO timestamp with explicit offset."""
        from services.audit_reader import _parse_timestamp

        result = _parse_timestamp("2026-01-01T10:00:00+00:00")
        assert result is not None
        assert result.tzinfo is not None

    def test_parse_date_only(self) -> None:
        """Should parse date-only string as start of day UTC."""
        from datetime import timezone

        from services.audit_reader import _parse_timestamp

        result = _parse_timestamp("2026-01-01")
        assert result is not None
        assert result.tzinfo == timezone.utc
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0

    def test_parse_naive_datetime(self) -> None:
        """Should parse naive datetime and assume UTC."""
        from datetime import timezone

        from services.audit_reader import _parse_timestamp

        result = _parse_timestamp("2026-01-01T10:00:00")
        assert result is not None
        assert result.tzinfo == timezone.utc

    def test_parse_empty_string(self) -> None:
        """Should return None for empty string."""
        from services.audit_reader import _parse_timestamp

        result = _parse_timestamp("")
        assert result is None

    def test_parse_invalid_format(self) -> None:
        """Should return None for invalid timestamp format."""
        from services.audit_reader import _parse_timestamp

        result = _parse_timestamp("not-a-timestamp")
        assert result is None

    def test_filter_since_with_date_only(self, tmp_path: Path) -> None:
        """Should correctly filter using date-only since parameter."""
        import json

        from services.audit_reader import AuditReaderService

        # Create project structure
        edison_logs = tmp_path / ".project" / "logs" / "edison"
        edison_logs.mkdir(parents=True)

        # Create audit log with entries on different dates
        entries = [
            {
                "ts": "2026-01-01T10:00:00Z",
                "event": "cli.invocation.end",
                "command": "old command",
                "exit_code": 0,
            },
            {
                "ts": "2026-01-02T10:00:00Z",
                "event": "cli.invocation.end",
                "command": "new command",
                "exit_code": 0,
            },
        ]
        audit_path = edison_logs / "audit.jsonl"
        with open(audit_path, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        service = AuditReaderService(tmp_path)
        # Filter since 2026-01-02 (date only)
        result = service.read_audit_events(since="2026-01-02")

        # Should only include the entry from 2026-01-02
        assert len(result.items) == 1
        assert result.items[0].command == "new command"


class TestActivityPaginationWithFiltering:
    """Test correct pagination when filtering is applied."""

    def test_event_type_filter_before_limit(self, tmp_path: Path) -> None:
        """Event type filtering should be applied before limiting for correct pagination."""
        import json

        from services.audit_reader import AuditReaderService

        # Create project structure
        edison_logs = tmp_path / ".project" / "logs" / "edison"
        edison_logs.mkdir(parents=True)

        # Create audit log with mixed event types
        # If filtering happens after limiting, we'd get wrong results
        entries = []
        for i in range(10):
            # 5 entries with "session create" command
            entries.append({
                "ts": f"2026-01-01T{10+i:02d}:00:00Z",
                "event": "cli.invocation.end",
                "command": "session create",
                "exit_code": 0,
            })
            # 5 entries with "task claim" command
            entries.append({
                "ts": f"2026-01-01T{10+i:02d}:30:00Z",
                "event": "cli.invocation.end",
                "command": "task claim",
                "exit_code": 0,
            })

        audit_path = edison_logs / "audit.jsonl"
        with open(audit_path, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        service = AuditReaderService(tmp_path)

        # Request 3 items with event_type filter
        # If filter happens before limit: returns 3 "session.create" items, has_more=True
        # If filter happens after limit: would return fewer items incorrectly
        result = service.read_activity(event_type="session.create", limit=3)

        # Should get exactly 3 items
        assert len(result.items) == 3
        # All items should match the filter
        for item in result.items:
            assert item.event_type == "session.create"
        # Should indicate more items are available (5 total, only 3 returned)
        assert result.has_more is True

    def test_event_type_filter_has_more_false_when_exhausted(self, tmp_path: Path) -> None:
        """has_more should be False when all matching items are returned."""
        import json

        from services.audit_reader import AuditReaderService

        edison_logs = tmp_path / ".project" / "logs" / "edison"
        edison_logs.mkdir(parents=True)

        # Only 2 items with matching event type
        entries = [
            {
                "ts": "2026-01-01T10:00:00Z",
                "event": "cli.invocation.end",
                "command": "session create",
                "exit_code": 0,
            },
            {
                "ts": "2026-01-01T11:00:00Z",
                "event": "cli.invocation.end",
                "command": "session create",
                "exit_code": 0,
            },
            {
                "ts": "2026-01-01T12:00:00Z",
                "event": "cli.invocation.end",
                "command": "task claim",  # Different event type
                "exit_code": 0,
            },
        ]

        audit_path = edison_logs / "audit.jsonl"
        with open(audit_path, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        service = AuditReaderService(tmp_path)
        # Request up to 10 "session.create" items
        result = service.read_activity(event_type="session.create", limit=10)

        # Should get 2 items
        assert len(result.items) == 2
        # has_more should be False since we got all matching items
        assert result.has_more is False
