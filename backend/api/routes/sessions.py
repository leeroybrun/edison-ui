"""Session endpoints (T021/T041).

Implements session listing and guarded create/transition endpoints for a project.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from api.schemas.session_guards import (
    GuardFailure,
    GuardWarning,
    SessionCreatePreviewResponse,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionPreview,
    SessionTransitionPreviewResponse,
    SessionTransitionRequest,
    SessionTransitionResponse,
)
from api.schemas.sessions import (
    SessionGitInfo,
    SessionListItem,
    SessionListResponse,
)
from core.settings import get_settings
from models.actor import get_current_actor
from models.audit import AuditEntry, AuditTarget
from services.audit import AuditWriter
from services.project_discovery import ProjectDiscoveryService
from services.session_guard import SessionGuardService
from services.session_reader import SessionReaderService
from services.session_writer import SessionWriterService, generate_action_id

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
    try:
        all_sessions = session_reader.list_sessions(state=state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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


# =============================================================================
# Guarded Session Create Endpoints (T041)
# =============================================================================


@router.post("/create/preview", response_model=SessionCreatePreviewResponse)
async def preview_create_session(
    project_id: str,
    request: SessionCreateRequest,
) -> SessionCreatePreviewResponse:
    """Preview session creation (dry-run with guard checks).

    Returns validation result and preview of what would be created.
    """
    project_path = get_project_path(project_id)
    guard_service = SessionGuardService(project_path)

    # Run guard checks
    result = guard_service.check_create_guards(
        owner=request.owner,
        base_branch=request.base_branch,
    )

    # Convert to response
    failures = [GuardFailure(guard=f.guard, reason=f.reason) for f in result.failures]
    warnings = [GuardWarning(guard=w.guard, message=w.message) for w in result.warnings]

    # Create preview if valid
    preview = None
    if result.valid:
        preview = SessionPreview(
            owner=request.owner,
            base_branch=request.base_branch,
            initial_state="draft",
        )

    return SessionCreatePreviewResponse(
        valid=result.valid,
        guard_failures=failures,
        guard_warnings=warnings,
        preview=preview,
    )


@router.post("", response_model=SessionCreateResponse, status_code=201)
async def create_session(
    project_id: str,
    request: SessionCreateRequest,
) -> SessionCreateResponse:
    """Create a new session after preview confirmation.

    Requires confirmed=true in request body.
    """
    project_path = get_project_path(project_id)

    # Check confirmed flag
    if not request.confirmed:
        raise HTTPException(
            status_code=400,
            detail="Session creation requires confirmed=true. Use preview endpoint first.",
        )

    # Run guard checks
    guard_service = SessionGuardService(project_path)
    result = guard_service.check_create_guards(
        owner=request.owner,
        base_branch=request.base_branch,
    )

    if not result.valid:
        failures_detail = "; ".join(f"{f.guard}: {f.reason}" for f in result.failures)
        raise HTTPException(
            status_code=400,
            detail=f"Guard checks failed: {failures_detail}",
        )

    # Create the session
    writer_service = SessionWriterService(project_path)
    session_id = writer_service.create_session(
        owner=request.owner,
        base_branch=request.base_branch,
    )

    # Write audit entry
    action_id = generate_action_id()
    audit_writer = AuditWriter(project_path)
    actor = get_current_actor()
    entry = AuditEntry(
        action_id=action_id,
        actor=actor,
        timestamp=datetime.now(timezone.utc),
        action_type="session.create",
        target=AuditTarget(entity_type="session", entity_id=session_id),
        outcome="success",
        context={
            "owner": request.owner,
            "base_branch": request.base_branch,
        },
    )
    audit_writer.write_entry(entry)

    return SessionCreateResponse(
        session_id=session_id,
        audit_entry_id=action_id,
    )


# =============================================================================
# Guarded Session Transition Endpoints (T041)
# =============================================================================


@router.post(
    "/{session_id}/transition/preview", response_model=SessionTransitionPreviewResponse
)
async def preview_transition_session(
    project_id: str,
    session_id: str,
    request: SessionTransitionRequest,
) -> SessionTransitionPreviewResponse:
    """Preview session state transition (dry-run with guard checks).

    Returns validation result with current and target states.
    """
    project_path = get_project_path(project_id)
    guard_service = SessionGuardService(project_path)

    # Run guard checks
    result = guard_service.check_transition_guards(session_id, request.to_state)

    # Convert to response
    failures = [GuardFailure(guard=f.guard, reason=f.reason) for f in result.failures]
    warnings = [GuardWarning(guard=w.guard, message=w.message) for w in result.warnings]

    return SessionTransitionPreviewResponse(
        valid=result.valid,
        current_state=result.current_state,
        to_state=request.to_state,
        guard_failures=failures,
        guard_warnings=warnings,
    )


@router.post("/{session_id}/transition", response_model=SessionTransitionResponse)
async def transition_session(
    project_id: str,
    session_id: str,
    request: SessionTransitionRequest,
) -> SessionTransitionResponse:
    """Apply session state transition after preview confirmation.

    Requires confirmed=true in request body.
    """
    project_path = get_project_path(project_id)

    # Check confirmed flag
    if not request.confirmed:
        raise HTTPException(
            status_code=400,
            detail="Session transition requires confirmed=true. Use preview endpoint first.",
        )

    # Run guard checks
    guard_service = SessionGuardService(project_path)
    result = guard_service.check_transition_guards(session_id, request.to_state)

    if not result.valid:
        failures_detail = "; ".join(f"{f.guard}: {f.reason}" for f in result.failures)
        raise HTTPException(
            status_code=400,
            detail=f"Guard checks failed: {failures_detail}",
        )

    # Apply the transition
    writer_service = SessionWriterService(project_path)
    previous_state = writer_service.transition_session(session_id, request.to_state)

    # Write audit entry
    action_id = generate_action_id()
    audit_writer = AuditWriter(project_path)
    actor = get_current_actor()
    entry = AuditEntry(
        action_id=action_id,
        actor=actor,
        timestamp=datetime.now(timezone.utc),
        action_type="session.transition",
        target=AuditTarget(entity_type="session", entity_id=session_id),
        outcome="success",
        context={
            "from_state": previous_state,
            "to_state": request.to_state,
        },
    )
    audit_writer.write_entry(entry)

    return SessionTransitionResponse(
        session_id=session_id,
        previous_state=previous_state,
        new_state=request.to_state,
        audit_entry_id=action_id,
    )
