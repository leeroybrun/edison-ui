"""Session guard-related Pydantic schemas (T041).

Implements schemas for guarded session create/transition endpoints per api.md contract.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


# =============================================================================
# Guard Schemas (reuse pattern from tasks)
# =============================================================================


class GuardFailure(BaseModel):
    """A guard check that failed.

    Represents a blocking issue that prevents an operation.
    """

    guard: str
    reason: str


class GuardWarning(BaseModel):
    """A warning from a guard check (non-blocking)."""

    guard: str
    message: str


# =============================================================================
# Session Create Schemas
# =============================================================================


class SessionCreateRequest(BaseModel):
    """Request body for session creation.

    Used for both preview and apply endpoints.
    """

    owner: str | None = None
    base_branch: str = Field(..., alias="baseBranch")
    confirmed: bool = False

    model_config = {"populate_by_name": True}


class SessionPreview(BaseModel):
    """Preview of what session would be created."""

    owner: str | None = None
    base_branch: str = Field(..., alias="baseBranch")
    initial_state: str = Field("draft", alias="initialState")

    model_config = {"populate_by_name": True}


class SessionCreatePreviewResponse(BaseModel):
    """Response for session create preview endpoint.

    Returns validation result and preview of what would be created.
    """

    valid: bool
    guard_failures: list[GuardFailure] = Field(
        default_factory=list, alias="guardFailures"
    )
    guard_warnings: list[GuardWarning] = Field(
        default_factory=list, alias="guardWarnings"
    )
    preview: SessionPreview | None = None

    model_config = {"populate_by_name": True}


class SessionCreateResponse(BaseModel):
    """Response for session create (apply) endpoint."""

    session_id: str = Field(..., alias="sessionId")
    audit_entry_id: str = Field(..., alias="auditEntryId")

    model_config = {"populate_by_name": True}


# =============================================================================
# Session Transition Schemas
# =============================================================================


class SessionTransitionRequest(BaseModel):
    """Request body for session state transition.

    Used for both preview and apply endpoints.
    """

    to_state: str = Field(..., alias="toState")
    confirmed: bool = False

    model_config = {"populate_by_name": True}


class SessionTransitionPreviewResponse(BaseModel):
    """Response for session transition preview endpoint."""

    valid: bool
    current_state: str | None = Field(None, alias="currentState")
    to_state: str = Field(..., alias="toState")
    guard_failures: list[GuardFailure] = Field(
        default_factory=list, alias="guardFailures"
    )
    guard_warnings: list[GuardWarning] = Field(
        default_factory=list, alias="guardWarnings"
    )

    model_config = {"populate_by_name": True}


class SessionTransitionResponse(BaseModel):
    """Response for session transition (apply) endpoint."""

    session_id: str = Field(..., alias="sessionId")
    previous_state: str = Field(..., alias="previousState")
    new_state: str = Field(..., alias="newState")
    audit_entry_id: str = Field(..., alias="auditEntryId")

    model_config = {"populate_by_name": True}
