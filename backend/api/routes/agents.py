"""Agent tracking endpoints (T072).

Implements agent tracking endpoints for monitoring active runs and process events.
Best-effort, fail-open: returns empty results on errors instead of crashing.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from api.schemas.agents import (
    AgentActiveResponse,
    ProcessesResponse,
    ProcessEventsResponse,
    ProcessEvent,
    TrackingRun,
)
from core.settings import get_settings
from services.agent_tracking import AgentTrackingService
from services.project_discovery import ProjectDiscoveryService

router = APIRouter(prefix="/projects/{project_id}/agents", tags=["agents"])


def get_discovery_service() -> ProjectDiscoveryService:
    """Get a configured project discovery service."""
    settings = get_settings()
    return ProjectDiscoveryService(
        scan_roots=settings.get_expanded_scan_roots(),
        ignore_patterns=settings.scan_ignore_patterns,
        pin_storage_path=settings.get_expanded_pin_storage_path(),
    )


def validate_project_exists(project_id: str) -> str:
    """Validate that project exists and return its path.

    Args:
        project_id: The project ID to validate.

    Returns:
        The project path.

    Raises:
        HTTPException: If project not found.
    """
    service = get_discovery_service()
    project = service.get_project_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project.path


@router.get("/active", response_model=AgentActiveResponse)
async def list_active_agents(
    project_id: str,
    sessionId: Annotated[str | None, Query(description="Filter by session ID")] = None,
    taskId: Annotated[str | None, Query(description="Filter by task ID")] = None,
    type: Annotated[
        str | None, Query(description="Filter by type (implementation, validation, orchestrator)")
    ] = None,
) -> AgentActiveResponse:
    """List active agent runs for a project.

    Returns agents that are currently running (not completed).
    Includes staleness information based on heartbeat recency.

    This endpoint is fail-open: returns empty list on errors.
    """
    project_path = validate_project_exists(project_id)

    try:
        tracking_service = AgentTrackingService(project_path)
        active_agents = tracking_service.get_active_agents(
            session_id=sessionId,
            task_id=taskId,
            agent_type=type,
        )

        items = [
            TrackingRun(
                run_id=agent.run_id,
                type=agent.type,
                task_id=agent.task_id,
                session_id=agent.session_id,
                validator_id=agent.validator_id,
                round=agent.round,
                model=agent.model,
                process_id=agent.process_id,
                hostname=agent.hostname,
                started_at=agent.started_at,
                last_active_at=agent.last_active_at,
                is_running=agent.is_running,
                is_stale=agent.is_stale,
                state=agent.state,
            )
            for agent in active_agents
        ]

        return AgentActiveResponse(items=items, total=len(items))
    except Exception:
        # Fail-open: return empty list on any error
        return AgentActiveResponse(items=[], total=0)


@router.get("/processes", response_model=ProcessesResponse)
async def list_processes(
    project_id: str,
    sessionId: Annotated[str | None, Query(description="Filter by session ID")] = None,
) -> ProcessesResponse:
    """List all tracked processes for a project.

    Returns all processes including completed ones.
    Unlike /active, this includes agents that have finished.

    This endpoint is fail-open: returns empty list on errors.
    """
    project_path = validate_project_exists(project_id)

    try:
        tracking_service = AgentTrackingService(project_path)
        all_processes = tracking_service.get_all_processes(session_id=sessionId)

        items = [
            TrackingRun(
                run_id=agent.run_id,
                type=agent.type,
                task_id=agent.task_id,
                session_id=agent.session_id,
                validator_id=agent.validator_id,
                round=agent.round,
                model=agent.model,
                process_id=agent.process_id,
                hostname=agent.hostname,
                started_at=agent.started_at,
                last_active_at=agent.last_active_at,
                is_running=agent.is_running,
                is_stale=agent.is_stale,
                state=agent.state,
            )
            for agent in all_processes
        ]

        return ProcessesResponse(items=items, total=len(items))
    except Exception:
        # Fail-open: return empty list on any error
        return ProcessesResponse(items=[], total=0)


@router.get("/process-events", response_model=ProcessEventsResponse)
async def list_process_events(
    project_id: str,
    runId: Annotated[str | None, Query(description="Filter by run ID")] = None,
    since: Annotated[
        str | None, Query(description="Filter events since timestamp (ISO format)")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=500, description="Max items")] = 100,
) -> ProcessEventsResponse:
    """List raw process events for a project.

    Returns events from the process-events.jsonl log file.
    Useful for debugging and detailed tracking.

    This endpoint is fail-open: returns empty list on errors.
    """
    project_path = validate_project_exists(project_id)

    try:
        tracking_service = AgentTrackingService(project_path)
        events, has_more = tracking_service.get_process_events_paginated(
            run_id=runId,
            since=since,
            limit=limit,
        )

        items = [
            ProcessEvent(
                ts=event.ts,
                event=event.event,
                run_id=event.run_id,
                pid=event.pid,
                hostname=event.hostname,
                kind=event.kind,
                task_id=event.task_id,
                session_id=event.session_id,
                validator_id=event.validator_id,
                round=event.round,
                model=event.model,
            )
            for event in events
        ]

        return ProcessEventsResponse(items=items, has_more=has_more)
    except Exception:
        # Fail-open: return empty list on any error
        return ProcessEventsResponse(items=[], has_more=False)
