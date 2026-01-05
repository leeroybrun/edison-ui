"""QA endpoints (T030/T042).

Implements QA listing, detail, and validation trigger endpoints.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from api.schemas.qa import QADetail, QAListResponse
from api.schemas.validation_trigger import (
    GuardFailure,
    GuardWarning,
    ValidationTriggerPreviewRequest,
    ValidationTriggerPreviewResponse,
    ValidationTriggerRequest,
    ValidationTriggerResponse,
)
from api.routes.tasks import get_project_path
from models.actor import get_current_actor
from models.audit import AuditEntry, AuditTarget
from services.audit import AuditWriter
from services.qa_reader import QAReaderService
from services.validation_trigger import (
    ValidationTriggerGuardService,
    ValidationTriggerService,
    generate_action_id,
)

router = APIRouter(prefix="/projects/{project_id}", tags=["qa"])


@router.get("/qa", response_model=QAListResponse)
async def list_qa_records(
    project_id: str,
    session_id: Annotated[
        str | None, Query(alias="sessionId", description="Filter by session ID")
    ] = None,
    state: Annotated[str | None, Query(description="Filter by state")] = None,
    verdict: Annotated[str | None, Query(description="Filter by verdict")] = None,
    limit: Annotated[int, Query(ge=1, le=1000, description="Max items")] = 100,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
) -> QAListResponse:
    """List QA records for a project."""
    project_path = get_project_path(project_id)
    service = QAReaderService(project_path)

    all_records = service.list_qa_records(
        session_id=session_id,
        state=state,
        verdict=verdict,
    )

    total = len(all_records)
    paginated = all_records[offset : offset + limit]

    return QAListResponse(
        items=paginated,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/tasks/{task_id}/qa", response_model=QADetail)
async def get_qa_detail(
    project_id: str,
    task_id: str,
) -> QADetail:
    """Get QA detail for a specific task."""
    project_path = get_project_path(project_id)
    service = QAReaderService(project_path)

    detail = service.get_qa_detail(task_id)
    if not detail:
        raise HTTPException(
            status_code=404, detail=f"QA record not found for task {task_id}"
        )

    return detail


# =============================================================================
# Validation Trigger Endpoints (T042)
# =============================================================================


@router.post("/qa/trigger/preview", response_model=ValidationTriggerPreviewResponse)
async def preview_trigger_validation(
    project_id: str,
    request: ValidationTriggerPreviewRequest,
) -> ValidationTriggerPreviewResponse:
    """Preview triggering validation (dry-run with guard checks).

    Returns validation result and preview of what would be created.
    """
    project_path = get_project_path(project_id)
    guard_service = ValidationTriggerGuardService(project_path)

    # Run guard checks
    result = guard_service.check_trigger_guards(
        task_id=request.task_id,
        validators=request.validators,
    )

    # Convert to response
    failures = [GuardFailure(guard=f.guard, reason=f.reason) for f in result.failures]
    warnings = [GuardWarning(guard=w.guard, message=w.message) for w in result.warnings]

    return ValidationTriggerPreviewResponse(
        valid=result.valid,
        task_id=result.task_id,
        task_state=result.task_state,
        suggested_validators=result.suggested_validators,
        guard_failures=failures,
        guard_warnings=warnings,
    )


@router.post("/qa/trigger", response_model=ValidationTriggerResponse)
async def trigger_validation(
    project_id: str,
    request: ValidationTriggerRequest,
) -> ValidationTriggerResponse:
    """Trigger validation after preview confirmation.

    Requires confirmed=true in request body.
    """
    project_path = get_project_path(project_id)

    # Check confirmed flag
    if not request.confirmed:
        raise HTTPException(
            status_code=400,
            detail="Validation trigger requires confirmed=true. Use preview endpoint first.",
        )

    # Run guard checks
    guard_service = ValidationTriggerGuardService(project_path)
    result = guard_service.check_trigger_guards(
        task_id=request.task_id,
        validators=request.validators,
    )

    if not result.valid:
        failures_detail = "; ".join(f"{f.guard}: {f.reason}" for f in result.failures)
        raise HTTPException(
            status_code=400,
            detail=f"Guard checks failed: {failures_detail}",
        )

    # Trigger validation
    trigger_service = ValidationTriggerService(project_path)
    qa_id, round_number = trigger_service.trigger_validation(
        task_id=request.task_id,
        validators=request.validators,
    )

    # Write audit entry
    action_id = generate_action_id()
    audit_writer = AuditWriter(project_path)
    actor = get_current_actor()
    entry = AuditEntry(
        action_id=action_id,
        actor=actor,
        timestamp=datetime.now(timezone.utc),
        action_type="qa.trigger",
        target=AuditTarget(entity_type="qa", entity_id=qa_id),
        outcome="success",
        context={
            "task_id": request.task_id,
            "validators": request.validators,
            "round": round_number,
        },
    )
    audit_writer.write_entry(entry)

    return ValidationTriggerResponse(
        qa_id=qa_id,
        task_id=request.task_id,
        round=round_number,
        audit_entry_id=action_id,
    )
