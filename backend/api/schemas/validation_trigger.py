"""Validation trigger schemas (T042).

Implements schemas for QA validation trigger preview/apply endpoints.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class GuardFailure(BaseModel):
    """A guard check that failed."""

    guard: str
    reason: str


class GuardWarning(BaseModel):
    """A warning from a guard check (non-blocking)."""

    guard: str
    message: str


class ValidationTriggerPreviewRequest(BaseModel):
    """Request for validation trigger preview."""

    task_id: str = Field(..., alias="taskId")
    validators: list[str] | None = None

    model_config = {"populate_by_name": True}


class ValidationTriggerPreviewResponse(BaseModel):
    """Response for validation trigger preview."""

    valid: bool
    task_id: str = Field(..., alias="taskId")
    task_state: str | None = Field(None, alias="taskState")
    suggested_validators: list[str] = Field(default_factory=list, alias="suggestedValidators")
    guard_failures: list[GuardFailure] = Field(default_factory=list, alias="guardFailures")
    guard_warnings: list[GuardWarning] = Field(default_factory=list, alias="guardWarnings")

    model_config = {"populate_by_name": True}


class ValidationTriggerRequest(BaseModel):
    """Request for validation trigger apply."""

    task_id: str = Field(..., alias="taskId")
    validators: list[str] | None = None
    confirmed: bool = False

    model_config = {"populate_by_name": True}


class ValidationTriggerResponse(BaseModel):
    """Response for validation trigger apply."""

    qa_id: str = Field(..., alias="qaId")
    task_id: str = Field(..., alias="taskId")
    round: int
    audit_entry_id: str = Field(..., alias="auditEntryId")

    model_config = {"populate_by_name": True}
