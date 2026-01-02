"""Session endpoints (T021).

Implements session listing endpoint for a project.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from api.schemas.sessions import (
    SessionGitInfo,
    SessionListItem,
    SessionListResponse,
)
from core.settings import get_settings
from services.project_discovery import ProjectDiscoveryService
from services.session_reader import SessionReaderService

router = APIRouter(prefix="/projects/{project_id}/sessions", tags=["sessions"])


def get_discovery_service() -> ProjectDiscoveryService:
    """Get a configured project discovery service."""
    settings = get_settings()
    return ProjectDiscoveryService(
        scan_roots=settings.get_expanded_scan_roots(),
        ignore_patterns=settings.scan_ignore_patterns,
        pin_storage_path=settings.get_expanded_pin_storage_path(),
    )


def get_project_path(project_id: str) -> str:
    """Get the absolute path for a project ID.

    Args:
        project_id: The project ID to look up.

    Returns:
        Absolute path to the project.

    Raises:
        HTTPException: If project not found.
    """
    service = get_discovery_service()
    project = service.get_project_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project.path


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    project_id: str,
    state: Annotated[str | None, Query(description="Filter by session state")] = None,
    limit: Annotated[int, Query(ge=1, le=1000, description="Max items")] = 100,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
) -> SessionListResponse:
    """List all sessions for a project."""
    project_path = get_project_path(project_id)

    session_reader = SessionReaderService(project_path)
    all_sessions = session_reader.list_sessions(state=state)

    # Get total before pagination
    total = len(all_sessions)

    # Apply pagination
    paginated = all_sessions[offset : offset + limit]

    # Convert to response items
    items = [
        SessionListItem(
            session_id=s.session_id,
            state=s.state,
            phase=s.phase,
            owner=s.owner,
            task_count=s.task_count,
            created_at=s.created_at,
            last_active_at=s.last_active_at,
            git=SessionGitInfo(
                branch_name=s.git.branch_name,
                base_branch=s.git.base_branch,
            ),
        )
        for s in paginated
    ]

    return SessionListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
