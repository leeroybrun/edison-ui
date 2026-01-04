"""Activity endpoints (T044).

Implements activity and audit endpoints for project activity timeline.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from api.schemas.activity import (
    ActivityResponse,
    AuditResponse,
)
from core.settings import get_settings
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
    since: Annotated[str | None, Query(description="Filter events since timestamp")] = None,
    limit: Annotated[int, Query(ge=1, le=500, description="Max items")] = 50,
) -> ActivityResponse:
    """Get activity timeline for a project.

    Returns a list of recent activity items for the project, optionally
    filtered by session, task, or event type.

    Note: Currently returns empty list. Full implementation will read
    from Edison audit log files.
    """
    # Validate project exists
    validate_project_exists(project_id)

    # TODO: Implement actual activity reading from Edison audit logs
    # For now, return empty list to allow frontend to render without errors
    return ActivityResponse(items=[], hasMore=False)


@router.get("/audit", response_model=AuditResponse)
async def get_audit(
    project_id: str,
    sessionId: Annotated[str | None, Query(description="Filter by session ID")] = None,
    invocationId: Annotated[str | None, Query(description="Filter by invocation ID")] = None,
    since: Annotated[str | None, Query(description="Filter events since timestamp")] = None,
    limit: Annotated[int, Query(ge=1, le=500, description="Max items")] = 50,
) -> AuditResponse:
    """Get raw audit events for a project.

    Returns a list of audit events from the Edison audit log,
    optionally filtered by session or invocation.

    Note: Currently returns empty list. Full implementation will read
    from Edison audit log files.
    """
    # Validate project exists
    validate_project_exists(project_id)

    # TODO: Implement actual audit log reading
    # For now, return empty list to allow frontend to render without errors
    return AuditResponse(items=[], hasMore=False)
