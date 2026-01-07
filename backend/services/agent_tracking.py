"""Agent tracking service (T072).

Parses process-events.jsonl and tracks active/stale agents.
Best-effort, fail-open: returns empty results on errors.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Literal


# Default staleness threshold in seconds (120s = 2 minutes)
DEFAULT_STALE_THRESHOLD_SECONDS = 120


@dataclass
class ProcessEventData:
    """Parsed process event from JSONL."""

    ts: str
    event: str
    run_id: str
    pid: int | None = None
    hostname: str | None = None
    kind: str | None = None
    task_id: str | None = None
    session_id: str | None = None
    validator_id: str | None = None
    round: int | None = None
    model: str | None = None


@dataclass
class ActiveAgentData:
    """Computed active agent data."""

    run_id: str
    type: Literal["implementation", "validation", "orchestrator"]
    task_id: str | None = None
    session_id: str | None = None
    validator_id: str | None = None
    round: int | None = None
    model: str | None = None
    process_id: int = 0
    hostname: str = "unknown"
    started_at: str = ""
    last_active_at: str = ""
    is_running: bool = True
    is_stale: bool = False
    state: Literal["active", "stopped"] = "active"


class AgentTrackingService:
    """Service for tracking agent processes from process-events.jsonl.

    This service is fail-open: if the JSONL file doesn't exist or is malformed,
    it returns empty results rather than raising errors.
    """

    def __init__(
        self,
        project_path: str,
        stale_threshold_seconds: int = DEFAULT_STALE_THRESHOLD_SECONDS,
    ) -> None:
        """Initialize the agent tracking service.

        Args:
            project_path: Absolute path to the Edison project root.
            stale_threshold_seconds: Seconds after which an agent is considered stale
                                     if no heartbeat is received.
        """
        self.project_path = Path(project_path)
        self.stale_threshold_seconds = stale_threshold_seconds
        self._events_cache: list[ProcessEventData] | None = None

    def _get_process_events_path(self) -> Path:
        """Get the path to process-events.jsonl.

        Returns:
            Path to the JSONL file.
        """
        return self.project_path / ".project" / "logs" / "edison" / "process-events.jsonl"

    def _parse_event(self, line: str) -> ProcessEventData | None:
        """Parse a single JSONL line into a ProcessEventData.

        Args:
            line: A single line from the JSONL file.

        Returns:
            ProcessEventData or None if parsing fails.
        """
        try:
            data: dict[str, Any] = json.loads(line)
        except json.JSONDecodeError:
            return None

        # Required fields
        ts = data.get("ts")
        event = data.get("event")
        run_id = data.get("runId")

        if not ts or not event or not run_id:
            return None

        return ProcessEventData(
            ts=str(ts),
            event=str(event),
            run_id=str(run_id),
            pid=data.get("pid"),
            hostname=data.get("hostname"),
            kind=data.get("kind"),
            task_id=data.get("taskId"),
            session_id=data.get("sessionId"),
            validator_id=data.get("validatorId"),
            round=data.get("round"),
            model=data.get("model"),
        )

    def _load_events(self) -> list[ProcessEventData]:
        """Load all events from the JSONL file.

        Returns:
            List of parsed events. Empty list on any error.
        """
        if self._events_cache is not None:
            return self._events_cache

        events: list[ProcessEventData] = []
        jsonl_path = self._get_process_events_path()

        if not jsonl_path.exists():
            self._events_cache = events
            return events

        try:
            content = jsonl_path.read_text(encoding="utf-8")
        except OSError:
            self._events_cache = events
            return events

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            event = self._parse_event(line)
            if event:
                events.append(event)

        self._events_cache = events
        return events

    def get_process_events(
        self,
        run_id: str | None = None,
        since: str | None = None,
        limit: int | None = None,
    ) -> list[ProcessEventData]:
        """Get process events with optional filtering.

        Args:
            run_id: Filter by run ID.
            since: Filter events since this ISO timestamp.
            limit: Maximum number of events to return (None = no limit).

        Returns:
            List of filtered events.
        """
        all_events = self._load_events()
        filtered: list[ProcessEventData] = []

        for event in all_events:
            # Filter by run_id
            if run_id and event.run_id != run_id:
                continue

            # Filter by since timestamp
            if since and event.ts < since:
                continue

            filtered.append(event)

        # Sort by timestamp descending (newest first)
        filtered.sort(key=lambda e: e.ts, reverse=True)

        # Apply limit if specified
        if limit is not None:
            filtered = filtered[:limit]

        return filtered

    def get_process_events_paginated(
        self,
        run_id: str | None = None,
        since: str | None = None,
        limit: int = 100,
    ) -> tuple[list[ProcessEventData], bool]:
        """Get process events with pagination support.

        Args:
            run_id: Filter by run ID.
            since: Filter events since this ISO timestamp.
            limit: Maximum number of events to return.

        Returns:
            Tuple of (list of events, has_more flag).
        """
        # Get one more than limit to check if there are more
        events = self.get_process_events(run_id=run_id, since=since, limit=limit + 1)
        has_more = len(events) > limit
        return events[:limit], has_more

    def _map_kind_to_type(
        self, kind: str | None
    ) -> Literal["implementation", "validation", "orchestrator"]:
        """Map event kind to run type.

        Args:
            kind: The kind from the event.

        Returns:
            The run type.
        """
        if kind == "validation":
            return "validation"
        if kind == "orchestrator":
            return "orchestrator"
        # Default to implementation for unknown or "implementation"
        return "implementation"

    def _compute_agents_from_events(
        self,
    ) -> dict[str, ActiveAgentData]:
        """Compute agent states from all events.

        Returns:
            Dictionary mapping run_id to ActiveAgentData.
        """
        events = self._load_events()
        agents: dict[str, ActiveAgentData] = {}
        completed_runs: set[str] = set()

        # Sort events by timestamp to process in order
        sorted_events = sorted(events, key=lambda e: e.ts)

        for event in sorted_events:
            run_id = event.run_id

            if event.event == "started":
                # Initialize or update agent
                agent = ActiveAgentData(
                    run_id=run_id,
                    type=self._map_kind_to_type(event.kind),
                    task_id=event.task_id,
                    session_id=event.session_id,
                    validator_id=event.validator_id,
                    round=event.round,
                    model=event.model,
                    process_id=event.pid or 0,
                    hostname=event.hostname or "unknown",
                    started_at=event.ts,
                    last_active_at=event.ts,
                    is_running=True,
                    is_stale=False,
                    state="active",
                )
                agents[run_id] = agent

            elif event.event == "heartbeat":
                # Update last_active_at
                if run_id in agents:
                    agents[run_id].last_active_at = event.ts

            elif event.event == "completed":
                # Mark as completed
                completed_runs.add(run_id)
                if run_id in agents:
                    agents[run_id].is_running = False
                    agents[run_id].state = "stopped"
                    agents[run_id].last_active_at = event.ts

        # Compute staleness for running agents
        now = datetime.now(timezone.utc)
        threshold = timedelta(seconds=self.stale_threshold_seconds)

        for run_id, agent in agents.items():
            if run_id in completed_runs:
                continue

            # Parse last_active_at to check staleness
            try:
                # Handle ISO format with or without timezone
                last_active_str = agent.last_active_at
                if last_active_str.endswith("Z"):
                    last_active_str = last_active_str[:-1] + "+00:00"
                last_active = datetime.fromisoformat(last_active_str)
                if last_active.tzinfo is None:
                    last_active = last_active.replace(tzinfo=timezone.utc)

                if now - last_active > threshold:
                    agent.is_stale = True
            except (ValueError, TypeError):
                # If we can't parse the timestamp, assume not stale
                pass

        return agents

    def get_active_agents(
        self,
        session_id: str | None = None,
        task_id: str | None = None,
        agent_type: str | None = None,
    ) -> list[ActiveAgentData]:
        """Get list of active (non-completed) agents.

        Args:
            session_id: Filter by session ID.
            task_id: Filter by task ID.
            agent_type: Filter by agent type (implementation, validation, orchestrator).

        Returns:
            List of active agents.
        """
        agents = self._compute_agents_from_events()
        result: list[ActiveAgentData] = []

        for agent in agents.values():
            # Only include running agents (not completed)
            if not agent.is_running:
                continue

            # Filter by session_id
            if session_id and agent.session_id != session_id:
                continue

            # Filter by task_id
            if task_id and agent.task_id != task_id:
                continue

            # Filter by type
            if agent_type and agent.type != agent_type:
                continue

            result.append(agent)

        return result

    def get_all_processes(
        self,
        session_id: str | None = None,
    ) -> list[ActiveAgentData]:
        """Get list of all tracked processes (including completed).

        Args:
            session_id: Filter by session ID.

        Returns:
            List of all processes.
        """
        agents = self._compute_agents_from_events()
        result: list[ActiveAgentData] = []

        for agent in agents.values():
            # Filter by session_id
            if session_id and agent.session_id != session_id:
                continue

            result.append(agent)

        return result

    def invalidate_cache(self) -> None:
        """Clear the internal cache to force reload on next access."""
        self._events_cache = None
