"""QA endpoints (T030).

Implements QA listing and detail endpoints.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from api.schemas.qa import QADetail, QAListResponse
from api.routes.tasks import get_project_path
from services.qa_reader import QAReaderService

router = APIRouter(prefix="/projects/{project_id}", tags=["qa"])


@router.get("/qa", response_model=QAListResponse)
async def list_qa_records(
    project_id: str,
    session_id: Annotated[
        str | None, Query(alias="sessionId", description="Filter by session ID")
    ] = None,
    state: Annotated[
        str | None, Query(description="Filter by state")
    ] = None,
    verdict: Annotated[
        str | None, Query(description="Filter by verdict")
    ] = None,
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
        raise HTTPException(status_code=404, detail=f"QA record not found for task {task_id}")

    return detail
