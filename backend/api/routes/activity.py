"""Activity endpoints (T044, T078).

Implements activity and audit endpoints for project activity timeline.
T078: Reads from Edison JSONL audit logs with filtering + pagination.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from api.schemas.activity import (
    ActivityItem,
    ActivityResponse,
    AuditEvent,
    AuditResponse,
)
from core.settings import get_settings
from services.audit_reader import AuditReaderService
from services.project_discovery import ProjectDiscoveryService

router = APIRouter(prefix="/projects/{project_id}", tags=["activity"])


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


@router.get("/activity", response_model=ActivityResponse)
async def get_activity(
    project_id: str,
    sessionId: Annotated[str | None, Query(description="Filter by session ID")] = None,
    taskId: Annotated[str | None, Query(description="Filter by task ID")] = None,
    eventType: Annotated[str | None, Query(description="Filter by event type")] = None,
    since: Annotated[
        str | None, Query(description="Filter events since timestamp")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=500, description="Max items")] = 50,
    offset: Annotated[int, Query(ge=0, description="Items to skip")] = 0,
) -> ActivityResponse:
    """Get activity timeline for a project.

    Returns a list of recent activity items for the project, optionally
    filtered by session, task, or event type.

    Reads from Edison JSONL audit logs and converts CLI invocations
    into high-level activity items.
    """
    # Validate project exists and get path
    project_path = validate_project_exists(project_id)

    # Read activity from audit logs
    reader = AuditReaderService(project_path)
    result = reader.read_activity(
        session_id=sessionId,
        task_id=taskId,
        event_type=eventType,
        since=since,
        limit=limit,
        offset=offset,
    )

    # Convert to API schema
    items = [
        ActivityItem(
            timestamp=item.timestamp,
            eventType=item.event_type,
            summary=item.summary,
            sessionId=item.session_id,
            taskId=item.task_id,
            invocationId=item.invocation_id,
            actor=None,  # Edison audit logs don't include actor info
        )
        for item in result.items
    ]

    return ActivityResponse(items=items, hasMore=result.has_more)


@router.get("/audit", response_model=AuditResponse)
async def get_audit(
    project_id: str,
    sessionId: Annotated[str | None, Query(description="Filter by session ID")] = None,
    invocationId: Annotated[
        str | None, Query(description="Filter by invocation ID")
    ] = None,
    since: Annotated[
        str | None, Query(description="Filter events since timestamp")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=500, description="Max items")] = 50,
    offset: Annotated[int, Query(ge=0, description="Items to skip")] = 0,
) -> AuditResponse:
    """Get raw audit events for a project.

    Returns a list of audit events from the Edison audit log,
    optionally filtered by session or invocation.

    Reads directly from Edison JSONL audit logs with automatic
    redaction of sensitive paths.
    """
    # Validate project exists and get path
    project_path = validate_project_exists(project_id)

    # Read audit events
    reader = AuditReaderService(project_path)
    result = reader.read_audit_events(
        session_id=sessionId,
        invocation_id=invocationId,
        since=since,
        limit=limit,
        offset=offset,
    )

    # Convert to API schema
    items = [
        AuditEvent(
            ts=item.ts,
            event=item.event,
            invocationId=item.invocation_id,
            sessionId=item.session_id,
            taskId=item.task_id,
            command=item.command,
            exitCode=item.exit_code,
            durationMs=item.duration_ms,
            projectRoot=item.project_root,
            pid=item.pid,
        )
        for item in result.items
    ]

    return AuditResponse(items=items, hasMore=result.has_more)
