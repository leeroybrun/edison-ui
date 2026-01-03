"""Task endpoints (T020/T022).

Implements task listing and readiness endpoints per api.md contracts.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from api.schemas.tasks import (
    BlockedByItem,
    GuardBlock,
    TaskListItem,
    TaskListResponse,
    TaskReadinessResponse,
)
from core.settings import get_settings
from services.project_discovery import ProjectDiscoveryService
from services.task_reader import TaskReaderService

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])


def get_discovery_service() -> ProjectDiscoveryService:
    """Get a configured project discovery service."""
    settings = get_settings()
    return ProjectDiscoveryService(
        scan_roots=settings.get_expanded_scan_roots(),
        ignore_patterns=settings.scan_ignore_patterns,
        pin_storage_path=settings.get_expanded_pin_storage_path(),
    )


def get_project_path(project_id: str) -> str:
    """Get the project path from project ID.

    Args:
        project_id: The project ID.

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


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    project_id: str,
    session_id: Annotated[
        str | None, Query(alias="sessionId", description="Filter by session ID")
    ] = None,
    state: Annotated[
        str | None, Query(description="Filter by state(s), comma-separated")
    ] = None,
    validation_status: Annotated[
        str | None,
        Query(alias="validationStatus", description="Filter by validation status"),
    ] = None,
    parent_id: Annotated[
        str | None, Query(alias="parentId", description="Filter by parent task")
    ] = None,
    search: Annotated[str | None, Query(description="Full-text search")] = None,
    limit: Annotated[int, Query(ge=1, le=1000, description="Max items")] = 100,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
    include_hierarchy: Annotated[
        bool, Query(alias="includeHierarchy", description="Include hierarchy fields")
    ] = False,
) -> TaskListResponse:
    """List tasks for a project.

    Returns all tasks including both global tasks and session-scoped tasks.
    """
    project_path = get_project_path(project_id)
    task_service = TaskReaderService(project_path)

    # Parse states if comma-separated
    states_list: list[str] | None = None
    if state:
        states_list = [s.strip() for s in state.split(",") if s.strip()]

    # Get filtered tasks
    all_tasks = task_service.list_tasks(
        session_id=session_id,
        states=states_list,
        validation_status=validation_status,
        parent_id=parent_id,
        search=search,
    )

    # Get total before pagination
    total = len(all_tasks)

    # Apply pagination
    paginated = all_tasks[offset : offset + limit]

    # Convert to response items
    items: list[TaskListItem] = []
    for task in paginated:
        # Compute readiness
        readiness = task_service.compute_readiness(task.task_id)
        blocked_by_items = [
            BlockedByItem(
                dependency_id=b.dependency_id,
                dependency_state=b.dependency_state,
                required_states=b.required_states,
                reason=b.reason,
            )
            for b in readiness.blocked_by
        ]

        # Get validation status
        val_status = task_service.get_validation_status(task.task_id)

        item = TaskListItem(
            task_id=task.task_id,
            title=task.title,
            state=task.state,
            session_id=task.session_id,
            parent_id=task.parent_id if include_hierarchy else None,
            child_ids=task.child_ids if include_hierarchy else [],
            depends_on=task.depends_on if include_hierarchy else [],
            blocks_tasks=task.blocks_tasks if include_hierarchy else [],
            validation_status=val_status,
            latest_verdict=None,  # Placeholder - QA verdict computation is out of scope
            ready=readiness.ready,
            blocked_by=blocked_by_items,
            created_at=task.created_at or "1970-01-01T00:00:00Z",
            updated_at=task.updated_at or "1970-01-01T00:00:00Z",
        )
        items.append(item)

    return TaskListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{task_id}/readiness", response_model=TaskReadinessResponse)
async def get_task_readiness(project_id: str, task_id: str) -> TaskReadinessResponse:
    """Get computed readiness for a task.

    Returns readiness status based on dependency graph and guards.
    """
    project_path = get_project_path(project_id)
    task_service = TaskReaderService(project_path)

    # Check if task exists
    task = task_service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Compute readiness
    readiness = task_service.compute_readiness(task_id)

    # Convert to response
    blocked_by_items = [
        BlockedByItem(
            dependency_id=b.dependency_id,
            dependency_state=b.dependency_state,
            required_states=b.required_states,
            reason=b.reason,
        )
        for b in readiness.blocked_by
    ]

    guard_blocks = [
        GuardBlock(guard=g["guard"], reason=g["reason"]) for g in readiness.guard_blocks
    ]

    return TaskReadinessResponse(
        task_id=task_id,
        ready=readiness.ready,
        blocked_by=blocked_by_items,
        guard_blocks=guard_blocks,
    )
