"""Task endpoints (T020/T022/T040).

Implements task listing, readiness, and guarded create/transition endpoints per api.md contracts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from api.schemas.tasks import (
    BlockedByItem,
    GuardBlock,
    GuardFailure,
    GuardWarning,
    TaskCreatePreviewResponse,
    TaskCreateRequest,
    TaskCreateResponse,
    TaskListItem,
    TaskListResponse,
    TaskPreview,
    TaskReadinessResponse,
    TaskTransitionPreviewResponse,
    TaskTransitionRequest,
    TaskTransitionResponse,
    ValidationSummary,
)
from core.settings import get_settings
from models.actor import get_current_actor
from models.audit import AuditEntry, AuditTarget
from services.audit import AuditWriter
from services.project_discovery import ProjectDiscoveryService
from services.task_guard import TaskGuardService
from services.task_reader import TaskReaderService
from services.task_writer import TaskWriterService, generate_action_id

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

        # Get validation info
        val_summary = task_service.get_validation_summary(task.task_id)
        validation = ValidationSummary(
            status=val_summary.status,
            last_round=val_summary.last_round,
            validator_count=val_summary.validator_count,
            last_updated=val_summary.last_updated,
        )

        item = TaskListItem(
            task_id=task.task_id,
            title=task.title,
            state=task.state,
            session_id=task.session_id,
            parent_id=task.parent_id if include_hierarchy else None,
            child_ids=task.child_ids if include_hierarchy else [],
            depends_on=task.depends_on if include_hierarchy else [],
            blocks_tasks=task.blocks_tasks if include_hierarchy else [],
            validation_status=val_summary.status,
            validation=validation,
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


# =============================================================================
# Guarded Task Create Endpoints (T040)
# =============================================================================


@router.post("/preview", response_model=TaskCreatePreviewResponse)
async def preview_create_task(
    project_id: str,
    request: TaskCreateRequest,
) -> TaskCreatePreviewResponse:
    """Preview task creation (dry-run with guard checks).

    Returns validation result and preview of what would be created.
    """
    project_path = get_project_path(project_id)
    guard_service = TaskGuardService(project_path)

    # Run guard checks
    result = guard_service.check_create_guards(
        title=request.title,
        task_type=request.type,
        session_id=request.session_id,
        parent_id=request.parent_id,
        depends_on=request.depends_on,
    )

    # Convert to response
    failures = [GuardFailure(guard=f.guard, reason=f.reason) for f in result.failures]
    warnings = [GuardWarning(guard=w.guard, message=w.message) for w in result.warnings]

    # Create preview if valid
    preview = None
    if result.valid:
        preview = TaskPreview(
            title=request.title,
            type=request.type,
            session_id=request.session_id,
            parent_id=request.parent_id,
            depends_on=request.depends_on,
            initial_state="todo",
        )

    return TaskCreatePreviewResponse(
        valid=result.valid,
        guard_failures=failures,
        guard_warnings=warnings,
        preview=preview,
    )


@router.post("", response_model=TaskCreateResponse, status_code=201)
async def create_task(
    project_id: str,
    request: TaskCreateRequest,
) -> TaskCreateResponse:
    """Create a new task after preview confirmation.

    Requires confirmed=true in request body.
    """
    project_path = get_project_path(project_id)

    # Check confirmed flag
    if not request.confirmed:
        raise HTTPException(
            status_code=400,
            detail="Task creation requires confirmed=true. Use preview endpoint first.",
        )

    # Run guard checks
    guard_service = TaskGuardService(project_path)
    result = guard_service.check_create_guards(
        title=request.title,
        task_type=request.type,
        session_id=request.session_id,
        parent_id=request.parent_id,
        depends_on=request.depends_on,
    )

    if not result.valid:
        failures_detail = "; ".join(f"{f.guard}: {f.reason}" for f in result.failures)
        raise HTTPException(
            status_code=400,
            detail=f"Guard checks failed: {failures_detail}",
        )

    # Create the task
    writer_service = TaskWriterService(project_path)
    task_id = writer_service.create_task(
        title=request.title,
        task_type=request.type,
        session_id=request.session_id,
        parent_id=request.parent_id,
        depends_on=request.depends_on,
    )

    # Write audit entry
    action_id = generate_action_id()
    audit_writer = AuditWriter(project_path)
    actor = get_current_actor()
    entry = AuditEntry(
        action_id=action_id,
        actor=actor,
        timestamp=datetime.now(timezone.utc),
        action_type="task.create",
        target=AuditTarget(entity_type="task", entity_id=task_id),
        outcome="success",
        context={
            "title": request.title,
            "type": request.type,
            "session_id": request.session_id,
            "parent_id": request.parent_id,
            "depends_on": request.depends_on,
        },
    )
    audit_writer.write_entry(entry)

    return TaskCreateResponse(
        task_id=task_id,
        audit_entry_id=action_id,
    )


# =============================================================================
# Guarded Task Transition Endpoints (T040)
# =============================================================================


@router.post(
    "/{task_id}/transition/preview", response_model=TaskTransitionPreviewResponse
)
async def preview_transition_task(
    project_id: str,
    task_id: str,
    request: TaskTransitionRequest,
) -> TaskTransitionPreviewResponse:
    """Preview task state transition (dry-run with guard checks).

    Returns validation result with current and target states.
    """
    project_path = get_project_path(project_id)
    guard_service = TaskGuardService(project_path)

    # Run guard checks
    result = guard_service.check_transition_guards(task_id, request.to_state)

    # Convert to response
    failures = [GuardFailure(guard=f.guard, reason=f.reason) for f in result.failures]
    warnings = [GuardWarning(guard=w.guard, message=w.message) for w in result.warnings]

    return TaskTransitionPreviewResponse(
        valid=result.valid,
        current_state=result.current_state,
        to_state=request.to_state,  # Use request value since it's always present
        guard_failures=failures,
        guard_warnings=warnings,
    )


@router.post("/{task_id}/transition", response_model=TaskTransitionResponse)
async def transition_task(
    project_id: str,
    task_id: str,
    request: TaskTransitionRequest,
) -> TaskTransitionResponse:
    """Apply task state transition after preview confirmation.

    Requires confirmed=true in request body.
    """
    project_path = get_project_path(project_id)

    # Check confirmed flag
    if not request.confirmed:
        raise HTTPException(
            status_code=400,
            detail="Task transition requires confirmed=true. Use preview endpoint first.",
        )

    # Run guard checks
    guard_service = TaskGuardService(project_path)
    result = guard_service.check_transition_guards(task_id, request.to_state)

    if not result.valid:
        failures_detail = "; ".join(f"{f.guard}: {f.reason}" for f in result.failures)
        raise HTTPException(
            status_code=400,
            detail=f"Guard checks failed: {failures_detail}",
        )

    # Apply the transition
    writer_service = TaskWriterService(project_path)
    previous_state = writer_service.transition_task(task_id, request.to_state)

    # Write audit entry
    action_id = generate_action_id()
    audit_writer = AuditWriter(project_path)
    actor = get_current_actor()
    entry = AuditEntry(
        action_id=action_id,
        actor=actor,
        timestamp=datetime.now(timezone.utc),
        action_type="task.transition",
        target=AuditTarget(entity_type="task", entity_id=task_id),
        outcome="success",
        context={
            "from_state": previous_state,
            "to_state": request.to_state,
        },
    )
    audit_writer.write_entry(entry)

    return TaskTransitionResponse(
        task_id=task_id,
        previous_state=previous_state,
        new_state=request.to_state,
        audit_entry_id=action_id,
    )
