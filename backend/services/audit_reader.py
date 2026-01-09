"""Audit reader service for reading Edison JSONL audit logs (T078).

AuditReaderService provides read access to Edison's append-only audit logs
with filtering, pagination, and automatic redaction of sensitive data.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def _parse_timestamp(ts: str) -> datetime | None:
    """Parse an ISO timestamp string to a timezone-aware datetime.

    Handles various formats:
    - Full ISO with Z suffix: 2025-12-27T10:00:00Z
    - Full ISO with offset: 2025-12-27T10:00:00+00:00
    - Date only: 2025-12-27 (assumes start of day UTC)
    - Naive datetime: 2025-12-27T10:00:00 (assumes UTC)

    Returns None if parsing fails.
    """
    if not ts:
        return None

    try:
        # Handle Z suffix
        ts_normalized = ts.replace("Z", "+00:00")

        # Try parsing as full ISO format
        dt = datetime.fromisoformat(ts_normalized)

        # If naive (no timezone), assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt
    except ValueError:
        pass

    # Try parsing as date only
    try:
        date_only = datetime.strptime(ts, "%Y-%m-%d")
        return date_only.replace(tzinfo=timezone.utc)
    except ValueError:
        pass

    return None


class AuditEventItem(BaseModel):
    """A single raw audit event from the JSONL log."""

    ts: str
    event: str
    invocation_id: str | None = None
    session_id: str | None = None
    task_id: str | None = None
    command: str | None = None
    exit_code: int | None = None
    duration_ms: float | None = None
    project_root: str | None = None
    pid: int | None = None


class AuditEventResult(BaseModel):
    """Result of reading audit events."""

    items: list[AuditEventItem]
    has_more: bool


class ActivityItem(BaseModel):
    """A high-level activity item derived from audit events."""

    timestamp: str
    event_type: str
    summary: str
    session_id: str | None = None
    task_id: str | None = None
    invocation_id: str | None = None


class ActivityResult(BaseModel):
    """Result of reading activity items."""

    items: list[ActivityItem]
    has_more: bool


def _is_external_path(value: str, project_root: Path) -> bool:
    """Check if a path is outside the project root."""
    if not value or not value.startswith("/"):
        return False

    try:
        resolved_value = Path(value).resolve()
        resolved_root = project_root.resolve()
        resolved_value.relative_to(resolved_root)
        return False
    except ValueError:
        return True
    except OSError:
        return True


def _redact_paths(entry: dict[str, Any], project_root: Path) -> dict[str, Any]:
    """Redact external paths in an audit entry."""
    result = entry.copy()

    # Fields that may contain paths
    path_fields = [
        "project_root",
        "stdout_path",
        "stderr_path",
        "stdlib_log_path",
        "cwd",
    ]

    for field in path_fields:
        if field in result and isinstance(result[field], str):
            if _is_external_path(result[field], project_root):
                result[field] = "[REDACTED_PATH]"

    return result


class AuditReaderService:
    """Service for reading Edison audit logs.

    Reads JSONL audit logs from .project/logs/edison/ directory
    with support for filtering and pagination.
    """

    def __init__(self, project_root: Path | str) -> None:
        """Initialize the audit reader.

        Args:
            project_root: Path to the project root directory.
        """
        self._project_root = Path(project_root).resolve()
        self._log_dir = self._project_root / ".project" / "logs" / "edison"

    def _get_audit_files(self) -> list[Path]:
        """Get all audit JSONL files sorted by name (newest first)."""
        if not self._log_dir.exists():
            return []

        files = []
        for f in self._log_dir.iterdir():
            if f.is_file() and f.suffix == ".jsonl":
                # Include audit.jsonl and audit-*.jsonl files
                if f.stem == "audit" or f.stem.startswith("audit-"):
                    files.append(f)

        # Sort by name descending (audit.jsonl should come first if it's the main log)
        return sorted(files, reverse=True)

    def _read_entries(self) -> list[dict[str, Any]]:
        """Read all entries from audit JSONL files."""
        entries = []

        for audit_file in self._get_audit_files():
            try:
                with open(audit_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                entry = json.loads(line)
                                entries.append(entry)
                            except json.JSONDecodeError:
                                # Skip malformed lines
                                continue
            except OSError:
                # Skip unreadable files
                continue

        return entries

    def read_audit_events(
        self,
        session_id: str | None = None,
        invocation_id: str | None = None,
        event_type: str | None = None,
        since: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> AuditEventResult:
        """Read raw audit events with optional filtering.

        Args:
            session_id: Filter by session ID.
            invocation_id: Filter by invocation ID.
            event_type: Filter by event type.
            since: Filter events since this ISO timestamp.
            limit: Maximum number of items to return.
            offset: Number of items to skip (for pagination).

        Returns:
            AuditEventResult with filtered items and pagination flag.
        """
        entries = self._read_entries()

        # Parse since timestamp if provided
        since_dt = _parse_timestamp(since) if since else None

        # Filter entries
        filtered: list[dict[str, Any]] = []
        for entry in entries:
            # Session ID filter
            if session_id is not None:
                if entry.get("session_id") != session_id:
                    continue

            # Invocation ID filter
            if invocation_id is not None:
                if entry.get("invocation_id") != invocation_id:
                    continue

            # Event type filter
            if event_type is not None:
                if entry.get("event") != event_type:
                    continue

            # Since timestamp filter
            if since_dt is not None:
                entry_ts = entry.get("ts")
                entry_dt = _parse_timestamp(entry_ts) if entry_ts else None
                if entry_dt is not None and entry_dt < since_dt:
                    continue

            filtered.append(entry)

        # Sort by timestamp descending (newest first)
        filtered.sort(
            key=lambda e: e.get("ts", ""), reverse=True
        )

        # Apply offset and limit for pagination
        total_after_offset = len(filtered) - offset
        has_more = total_after_offset > limit
        limited = filtered[offset : offset + limit]

        # Redact sensitive paths and convert to models
        items: list[AuditEventItem] = []
        for entry in limited:
            redacted = _redact_paths(entry, self._project_root)
            items.append(
                AuditEventItem(
                    ts=redacted.get("ts", ""),
                    event=redacted.get("event", ""),
                    invocation_id=redacted.get("invocation_id"),
                    session_id=redacted.get("session_id"),
                    task_id=redacted.get("task_id"),
                    command=redacted.get("command"),
                    exit_code=redacted.get("exit_code"),
                    duration_ms=redacted.get("duration_ms"),
                    project_root=redacted.get("project_root"),
                    pid=redacted.get("pid"),
                )
            )

        return AuditEventResult(items=items, has_more=has_more)

    def read_activity(
        self,
        session_id: str | None = None,
        task_id: str | None = None,
        event_type: str | None = None,
        since: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ActivityResult:
        """Read high-level activity items derived from audit events.

        This filters out low-level subprocess events and consolidates
        CLI invocation pairs into single activity items.

        Args:
            session_id: Filter by session ID.
            task_id: Filter by task ID.
            event_type: Filter by event type.
            since: Filter events since this ISO timestamp.
            limit: Maximum number of items to return.
            offset: Number of items to skip (for pagination).

        Returns:
            ActivityResult with activity items and pagination flag.
        """
        entries = self._read_entries()

        # Parse since timestamp if provided
        since_dt = _parse_timestamp(since) if since else None

        # Filter to CLI invocation end events only (they have exit_code)
        # This gives us complete invocations with outcome
        cli_events: list[dict[str, Any]] = []
        for entry in entries:
            event = entry.get("event", "")

            # Only CLI invocation end events (they have complete info)
            if event != "cli.invocation.end":
                continue

            # Session ID filter
            if session_id is not None:
                if entry.get("session_id") != session_id:
                    continue

            # Task ID filter
            if task_id is not None:
                if entry.get("task_id") != task_id:
                    continue

            # Since timestamp filter
            if since_dt is not None:
                entry_ts = entry.get("ts")
                entry_dt = _parse_timestamp(entry_ts) if entry_ts else None
                if entry_dt is not None and entry_dt < since_dt:
                    continue

            # Derive event type from command for filtering
            command = entry.get("command", "")
            event_type_derived = command.replace(" ", ".") if command else "unknown"

            # Filter by event_type if provided (do this before limiting)
            if event_type is not None:
                if event_type_derived != event_type:
                    continue

            cli_events.append(entry)

        # Sort by timestamp descending
        cli_events.sort(key=lambda e: e.get("ts", ""), reverse=True)

        # Apply offset and limit for pagination
        total_after_offset = len(cli_events) - offset
        has_more = total_after_offset > limit
        limited = cli_events[offset : offset + limit]

        # Convert to activity items
        items: list[ActivityItem] = []
        for entry in limited:
            command = entry.get("command", "")

            # Derive event type from command
            # e.g., "session create" -> "session.create"
            event_type_derived = command.replace(" ", ".") if command else "unknown"

            # Generate summary
            exit_code = entry.get("exit_code", 0)
            duration_ms = entry.get("duration_ms", 0)
            outcome = "succeeded" if exit_code == 0 else f"failed (exit {exit_code})"
            duration_str = f"{duration_ms:.0f}ms" if duration_ms else ""
            summary = f"{command} {outcome}"
            if duration_str:
                summary += f" in {duration_str}"

            items.append(
                ActivityItem(
                    timestamp=entry.get("ts", ""),
                    event_type=event_type_derived,
                    summary=summary,
                    session_id=entry.get("session_id"),
                    task_id=entry.get("task_id"),
                    invocation_id=entry.get("invocation_id"),
                )
            )

        return ActivityResult(items=items, has_more=has_more)
