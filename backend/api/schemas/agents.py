"""Agent tracking Pydantic schemas (T072).

Schemas for agent tracking endpoints including active runs, processes, and events.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# =============================================================================
# Core Types
# =============================================================================

RunType = Literal["implementation", "validation", "orchestrator"]
RunState = Literal["active", "stopped"]


# =============================================================================
# TrackingRun Schema
# =============================================================================


class TrackingRun(BaseModel):
    """Represents a tracking run (agent/validator instance).

    Tracks active or completed agent runs with liveness information.
    """

    run_id: str = Field(..., alias="runId")
    type: RunType
    task_id: str | None = Field(None, alias="taskId")
    session_id: str | None = Field(None, alias="sessionId")
    validator_id: str | None = Field(None, alias="validatorId")
    round: int | None = None
    model: str | None = None
    process_id: int = Field(..., alias="processId")
    hostname: str
    started_at: str = Field(..., alias="startedAt")
    last_active_at: str = Field(..., alias="lastActiveAt")
    is_running: bool = Field(..., alias="isRunning")
    is_stale: bool = Field(..., alias="isStale")
    state: RunState

    model_config = {"populate_by_name": True}


# =============================================================================
# ProcessEvent Schema
# =============================================================================


class ProcessEvent(BaseModel):
    """A single process event from the JSONL log.

    Events include: started, heartbeat, completed.
    """

    ts: str
    event: str
    run_id: str = Field(..., alias="runId")
    pid: int | None = None
    hostname: str | None = None
    kind: str | None = None
    task_id: str | None = Field(None, alias="taskId")
    session_id: str | None = Field(None, alias="sessionId")
    validator_id: str | None = Field(None, alias="validatorId")
    round: int | None = None
    model: str | None = None

    model_config = {"populate_by_name": True}


# =============================================================================
# Response Schemas
# =============================================================================


class AgentActiveResponse(BaseModel):
    """Response for GET /projects/{projectId}/agents/active.

    Returns list of active (non-completed) agent runs.
    """

    items: list[TrackingRun]
    total: int


class ProcessesResponse(BaseModel):
    """Response for GET /projects/{projectId}/agents/processes.

    Returns list of all tracked processes (including completed).
    """

    items: list[TrackingRun]
    total: int


class ProcessEventsResponse(BaseModel):
    """Response for GET /projects/{projectId}/agents/process-events.

    Returns list of raw process events from the JSONL log.
    """

    items: list[ProcessEvent]
    has_more: bool = Field(..., alias="hasMore")

    model_config = {"populate_by_name": True}
