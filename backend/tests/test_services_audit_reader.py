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
