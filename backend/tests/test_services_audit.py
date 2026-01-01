"""Tests for AuditWriter service and redaction.

TDD RED PHASE: These tests are written BEFORE implementation.
Expected: All tests should fail initially.

Tests cover:
- AuditWriter creates JSONL file in correct location
- Entries are appended (not overwritten)
- Redaction of paths outside project root
- Redaction of env vars in context
- Redaction of known secret patterns
- Filesystem confinement (can't write outside .project/)
- Thread-safe writes
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest


class TestRedaction:
    """Test redaction helper functions."""

    def test_redact_context_preserves_safe_values(self, tmp_path: Path) -> None:
        """redact_context should preserve values that don't need redaction."""
        from services.audit import redact_context

        context: dict[str, Any] = {
            "action": "task_claimed",
            "count": 42,
            "enabled": True,
        }
        project_root = str(tmp_path)

        result = redact_context(context, project_root)

        assert result["action"] == "task_claimed"
        assert result["count"] == 42
        assert result["enabled"] is True

    def test_redact_context_redacts_paths_outside_project_root(
        self, tmp_path: Path
    ) -> None:
        """Paths outside project root should be redacted."""
        from services.audit import redact_context

        context: dict[str, Any] = {
            "safe_path": str(tmp_path / "subdir" / "file.txt"),
            "unsafe_path": "/etc/passwd",
            "another_unsafe": "/home/user/.ssh/id_rsa",
        }
        project_root = str(tmp_path)

        result = redact_context(context, project_root)

        # Safe path within project root should be preserved
        assert result["safe_path"] == str(tmp_path / "subdir" / "file.txt")
        # Paths outside project root should be redacted
        assert result["unsafe_path"] == "[REDACTED_PATH]"
        assert result["another_unsafe"] == "[REDACTED_PATH]"

    def test_redact_context_redacts_env_var_values(self, tmp_path: Path) -> None:
        """Environment variable values should be redacted (keys preserved)."""
        from services.audit import redact_context

        context: dict[str, Any] = {
            "env": {
                "PATH": "/usr/bin:/bin",
                "HOME": "/home/user",
                "API_KEY": "secret123",
            },
            "normal_key": "normal_value",
        }
        project_root = str(tmp_path)

        result = redact_context(context, project_root)

        # Env dict should have keys preserved but values redacted
        assert "env" in result
        assert "PATH" in result["env"]
        assert result["env"]["PATH"] == "[REDACTED_ENV]"
        assert result["env"]["HOME"] == "[REDACTED_ENV]"
        assert result["env"]["API_KEY"] == "[REDACTED_ENV]"
        # Normal values are preserved
        assert result["normal_key"] == "normal_value"

    def test_redact_context_redacts_api_key_patterns(self, tmp_path: Path) -> None:
        """Known API key patterns should be redacted."""
        from services.audit import redact_context

        context: dict[str, Any] = {
            "api_key": "sk-abc123xyz",
            "token": "ghp_1234567890abcdef",
            "apiKey": "AKIAIOSFODNN7EXAMPLE",
            "secret": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "normal_text": "this is fine",
        }
        project_root = str(tmp_path)

        result = redact_context(context, project_root)

        assert result["api_key"] == "[REDACTED_SECRET]"
        assert result["token"] == "[REDACTED_SECRET]"
        assert result["apiKey"] == "[REDACTED_SECRET]"
        assert result["secret"] == "[REDACTED_SECRET]"
        assert result["normal_text"] == "this is fine"

    def test_redact_context_handles_nested_dicts(self, tmp_path: Path) -> None:
        """Nested dictionaries should be recursively redacted."""
        from services.audit import redact_context

        context: dict[str, Any] = {
            "nested": {
                "deep": {
                    "api_key": "secret123",
                    "path": "/etc/passwd",
                }
            }
        }
        project_root = str(tmp_path)

        result = redact_context(context, project_root)

        assert result["nested"]["deep"]["api_key"] == "[REDACTED_SECRET]"
        assert result["nested"]["deep"]["path"] == "[REDACTED_PATH]"

    def test_redact_context_handles_lists(self, tmp_path: Path) -> None:
        """Lists should have their items redacted appropriately."""
        from services.audit import redact_context

        context: dict[str, Any] = {
            "paths": ["/safe/path", "/etc/passwd"],
            "items": ["normal", {"api_key": "secret"}],
        }
        project_root = str(tmp_path / "safe")

        result = redact_context(context, project_root)

        # First path is outside, second is also outside
        assert result["paths"][0] == "[REDACTED_PATH]"
        assert result["paths"][1] == "[REDACTED_PATH]"
        assert result["items"][0] == "normal"
        assert result["items"][1]["api_key"] == "[REDACTED_SECRET]"

    def test_redact_context_handles_none_values(self, tmp_path: Path) -> None:
        """None values should be preserved."""
        from services.audit import redact_context

        context: dict[str, Any] = {
            "optional_field": None,
            "normal_field": "value",
        }
        project_root = str(tmp_path)

        result = redact_context(context, project_root)

        assert result["optional_field"] is None
        assert result["normal_field"] == "value"

    def test_redact_context_empty_dict(self, tmp_path: Path) -> None:
        """Empty dict should return empty dict."""
        from services.audit import redact_context

        context: dict[str, Any] = {}
        project_root = str(tmp_path)

        result = redact_context(context, project_root)

        assert result == {}


class TestAuditWriter:
    """Test AuditWriter class."""

    def test_audit_writer_creates_log_directory(self, tmp_path: Path) -> None:
        """AuditWriter should create the log directory if it doesn't exist."""
        from services.audit import AuditWriter

        project_root = tmp_path / "project"
        project_root.mkdir()

        writer = AuditWriter(project_root)

        log_dir = project_root / ".project" / "logs" / "edison"
        assert log_dir.exists()
        assert log_dir.is_dir()
        # Verify writer has correct log directory
        assert writer.log_dir == log_dir

    def test_audit_writer_creates_jsonl_file_on_first_write(
        self, tmp_path: Path
    ) -> None:
        """AuditWriter should create JSONL file when first entry is written."""
        from models import ActorIdentity, AuditEntry, AuditTarget
        from services.audit import AuditWriter

        project_root = tmp_path / "project"
        project_root.mkdir()

        writer = AuditWriter(project_root)
        entry = AuditEntry(
            action_id="ACT001",
            actor=ActorIdentity(os_user="testuser", display_name=None),
            timestamp=datetime.now(timezone.utc),
            action_type="test_action",
            target=AuditTarget(entity_type="task", entity_id="T001"),
            outcome="success",
            context=None,
        )

        writer.write_entry(entry)

        log_files = list((project_root / ".project" / "logs" / "edison").glob("*.jsonl"))
        assert len(log_files) == 1

    def test_audit_writer_appends_entries(self, tmp_path: Path) -> None:
        """Multiple entries should be appended to the same file."""
        from models import ActorIdentity, AuditEntry, AuditTarget
        from services.audit import AuditWriter

        project_root = tmp_path / "project"
        project_root.mkdir()

        writer = AuditWriter(project_root)

        for i in range(3):
            entry = AuditEntry(
                action_id=f"ACT00{i}",
                actor=ActorIdentity(os_user="testuser", display_name=None),
                timestamp=datetime.now(timezone.utc),
                action_type="test_action",
                target=AuditTarget(entity_type="task", entity_id=f"T00{i}"),
                outcome="success",
                context=None,
            )
            writer.write_entry(entry)

        log_files = list((project_root / ".project" / "logs" / "edison").glob("*.jsonl"))
        assert len(log_files) == 1

        with open(log_files[0]) as f:
            lines = f.readlines()

        assert len(lines) == 3
        # Verify each line is valid JSON
        for i, line in enumerate(lines):
            data = json.loads(line)
            assert data["action_id"] == f"ACT00{i}"

    def test_audit_writer_writes_valid_jsonl(self, tmp_path: Path) -> None:
        """Written entries should be valid JSONL format."""
        from models import ActorIdentity, AuditEntry, AuditTarget
        from services.audit import AuditWriter

        project_root = tmp_path / "project"
        project_root.mkdir()

        writer = AuditWriter(project_root)
        timestamp = datetime(2025, 12, 27, 12, 0, 0, tzinfo=timezone.utc)
        entry = AuditEntry(
            action_id="ACT001",
            actor=ActorIdentity(os_user="testuser", display_name="Test User"),
            timestamp=timestamp,
            action_type="task_claimed",
            target=AuditTarget(entity_type="task", entity_id="T001"),
            outcome="success",
            context={"previous_status": "todo"},
        )

        writer.write_entry(entry)

        log_files = list((project_root / ".project" / "logs" / "edison").glob("*.jsonl"))
        with open(log_files[0]) as f:
            line = f.readline()
            data = json.loads(line)

        assert data["action_id"] == "ACT001"
        assert data["actor"]["os_user"] == "testuser"
        assert data["actor"]["display_name"] == "Test User"
        assert data["action_type"] == "task_claimed"
        assert data["target"]["entity_type"] == "task"
        assert data["target"]["entity_id"] == "T001"
        assert data["outcome"] == "success"
        assert data["context"]["previous_status"] == "todo"

    def test_audit_writer_redacts_before_writing(self, tmp_path: Path) -> None:
        """AuditWriter should apply redaction to context before writing."""
        from models import ActorIdentity, AuditEntry, AuditTarget
        from services.audit import AuditWriter

        project_root = tmp_path / "project"
        project_root.mkdir()

        writer = AuditWriter(project_root)
        entry = AuditEntry(
            action_id="ACT001",
            actor=ActorIdentity(os_user="testuser", display_name=None),
            timestamp=datetime.now(timezone.utc),
            action_type="test_action",
            target=AuditTarget(entity_type="task", entity_id="T001"),
            outcome="success",
            context={
                "api_key": "sk-secret123",
                "external_path": "/etc/passwd",
                "env": {"HOME": "/home/user"},
            },
        )

        writer.write_entry(entry)

        log_files = list((project_root / ".project" / "logs" / "edison").glob("*.jsonl"))
        with open(log_files[0]) as f:
            data = json.loads(f.readline())

        assert data["context"]["api_key"] == "[REDACTED_SECRET]"
        assert data["context"]["external_path"] == "[REDACTED_PATH]"
        assert data["context"]["env"]["HOME"] == "[REDACTED_ENV]"

    def test_audit_writer_handles_none_context(self, tmp_path: Path) -> None:
        """AuditWriter should handle entries with None context."""
        from models import ActorIdentity, AuditEntry, AuditTarget
        from services.audit import AuditWriter

        project_root = tmp_path / "project"
        project_root.mkdir()

        writer = AuditWriter(project_root)
        entry = AuditEntry(
            action_id="ACT001",
            actor=ActorIdentity(os_user="testuser", display_name=None),
            timestamp=datetime.now(timezone.utc),
            action_type="test_action",
            target=AuditTarget(entity_type="task", entity_id="T001"),
            outcome="success",
            context=None,
        )

        writer.write_entry(entry)

        log_files = list((project_root / ".project" / "logs" / "edison").glob("*.jsonl"))
        with open(log_files[0]) as f:
            data = json.loads(f.readline())

        assert data["context"] is None


class TestFilesystemConfinement:
    """Test that AuditWriter is confined to .project/ directory."""

    def test_audit_writer_confines_to_project_logs(self, tmp_path: Path) -> None:
        """AuditWriter should only write to .project/logs/edison/."""
        from services.audit import AuditWriter

        project_root = tmp_path / "project"
        project_root.mkdir()

        writer = AuditWriter(project_root)

        assert writer.log_dir == project_root / ".project" / "logs" / "edison"
        assert str(writer.log_dir).startswith(str(project_root))

    def test_audit_writer_rejects_log_dir_outside_project(
        self, tmp_path: Path
    ) -> None:
        """AuditWriter should reject attempts to set log dir outside project."""
        from services.audit import AuditWriter, FilesystemConfinementError

        project_root = tmp_path / "project"
        project_root.mkdir()
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()

        # Should raise error when trying to create writer with confined path
        with pytest.raises(FilesystemConfinementError):
            AuditWriter(project_root, log_dir_override=outside_dir)

    def test_audit_writer_rejects_symlink_escape(self, tmp_path: Path) -> None:
        """AuditWriter should reject symlinks that escape project root."""
        from services.audit import AuditWriter, FilesystemConfinementError

        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / ".project" / "logs").mkdir(parents=True)

        # Create a symlink pointing outside
        escape_target = tmp_path / "escape"
        escape_target.mkdir()
        escape_link = project_root / ".project" / "logs" / "edison"
        escape_link.symlink_to(escape_target)

        with pytest.raises(FilesystemConfinementError):
            AuditWriter(project_root)

    def test_audit_writer_validates_resolved_path(self, tmp_path: Path) -> None:
        """AuditWriter should resolve and validate paths to prevent traversal."""
        from services.audit import AuditWriter

        project_root = tmp_path / "project"
        project_root.mkdir()

        writer = AuditWriter(project_root)

        # The resolved log_dir should be under project_root
        resolved = writer.log_dir.resolve()
        assert str(resolved).startswith(str(project_root.resolve()))


class TestThreadSafety:
    """Test thread-safe writes."""

    def test_concurrent_writes_are_not_corrupted(self, tmp_path: Path) -> None:
        """Concurrent writes should not corrupt the log file."""
        import threading

        from models import ActorIdentity, AuditEntry, AuditTarget
        from services.audit import AuditWriter

        project_root = tmp_path / "project"
        project_root.mkdir()

        writer = AuditWriter(project_root)
        num_threads = 10
        entries_per_thread = 10

        def write_entries(thread_id: int) -> None:
            for i in range(entries_per_thread):
                entry = AuditEntry(
                    action_id=f"T{thread_id}-{i}",
                    actor=ActorIdentity(os_user="testuser", display_name=None),
                    timestamp=datetime.now(timezone.utc),
                    action_type="test_action",
                    target=AuditTarget(entity_type="task", entity_id=f"T{thread_id}-{i}"),
                    outcome="success",
                    context=None,
                )
                writer.write_entry(entry)

        threads = [
            threading.Thread(target=write_entries, args=(i,))
            for i in range(num_threads)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Read all entries and verify none are corrupted
        log_files = list((project_root / ".project" / "logs" / "edison").glob("*.jsonl"))
        assert len(log_files) == 1

        with open(log_files[0]) as f:
            lines = f.readlines()

        assert len(lines) == num_threads * entries_per_thread

        # Each line should be valid JSON
        for line in lines:
            data = json.loads(line)
            assert "action_id" in data
            assert "actor" in data
            assert "timestamp" in data


class TestServicesExport:
    """Test that services are properly exported."""

    def test_audit_writer_exported_from_services_package(self) -> None:
        """AuditWriter should be importable from services package."""
        from services import AuditWriter

        assert AuditWriter is not None

    def test_redact_context_exported_from_services_package(self) -> None:
        """redact_context should be importable from services package."""
        from services import redact_context

        assert redact_context is not None

    def test_filesystem_confinement_error_exported(self) -> None:
        """FilesystemConfinementError should be importable from services package."""
        from services import FilesystemConfinementError

        assert FilesystemConfinementError is not None
