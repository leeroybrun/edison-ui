"""Project endpoints (T010).

Implements project discovery, listing, detail, and pin endpoints.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from api.schemas.projects import (
    PinRequest,
    PinResponse,
    ProjectConfig,
    ProjectDetail,
    ProjectHealth,
    ProjectListItem,
    ProjectListResponse,
)
from core.settings import get_settings
from services.project_discovery import ProjectDiscoveryService

router = APIRouter(prefix="/projects", tags=["projects"])


def get_discovery_service() -> ProjectDiscoveryService:
    """Get a configured project discovery service."""
    settings = get_settings()
    return ProjectDiscoveryService(
        scan_roots=settings.get_expanded_scan_roots(),
        ignore_patterns=settings.scan_ignore_patterns,
        pin_storage_path=settings.get_expanded_pin_storage_path(),
    )


def redact_path(path: str) -> str:
    """Redact a path for security.

    For now, we show relative path from scan root or redact sensitive parts.
    """
    settings = get_settings()
    scan_roots = settings.get_expanded_scan_roots()

    # Check if path is under any scan root
    for root in scan_roots:
        if path.startswith(root):
            # Return relative path from scan root
            relative = path[len(root) :].lstrip("/")
            return f"~/{relative}" if relative else "~"

    # If not in scan roots, redact completely
    return "[REDACTED_PATH]"


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    pinned: Annotated[bool | None, Query(description="Filter by pinned status")] = None,
    limit: Annotated[int, Query(ge=1, le=1000, description="Max items")] = 100,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
) -> ProjectListResponse:
    """List all discovered Edison projects."""
    service = get_discovery_service()
    all_projects = service.discover_projects()

    # Filter by pinned if specified
    if pinned is not None:
        all_projects = [p for p in all_projects if p.pinned == pinned]

    # Get total before pagination
    total = len(all_projects)

    # Apply pagination
    paginated = all_projects[offset : offset + limit]

    # Convert to response items
    items = [
        ProjectListItem(
            project_id=p.project_id,
            path=redact_path(p.path),
            name=p.name,
            pinned=p.pinned,
            health=ProjectHealth(
                task_count=p.health.task_count,
                session_count=p.health.session_count,
                qa_count=p.health.qa_count,
                active_count=p.health.active_count,
            ),
            last_activity_at=p.last_activity_at,
            has_git=p.has_git,
            errors=p.errors,
        )
        for p in paginated
    ]

    return ProjectListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(project_id: str) -> ProjectDetail:
    """Get project details."""
    service = get_discovery_service()
    project = service.get_project_by_id(project_id)

    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    settings = get_settings()

    return ProjectDetail(
        project_id=project.project_id,
        path=redact_path(project.path),
        name=project.name,
        pinned=project.pinned,
        health=ProjectHealth(
            task_count=project.health.task_count,
            session_count=project.health.session_count,
            qa_count=project.health.qa_count,
            active_count=project.health.active_count,
        ),
        last_activity_at=project.last_activity_at,
        has_git=project.has_git,
        errors=project.errors,
        config=ProjectConfig(
            scan_roots=settings.scan_roots,
            memory_enabled=False,  # Will be configurable later
        ),
    )


@router.patch("/{project_id}/pin", response_model=PinResponse)
async def pin_project(project_id: str, body: PinRequest) -> PinResponse:
    """Toggle project pin status."""
    service = get_discovery_service()

    success = service.set_pinned(project_id, body.pinned)
    if not success:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    return PinResponse(
        project_id=project_id,
        pinned=body.pinned,
    )
