"""Task-related Pydantic schemas (T020/T022/T040).

Implements schemas for task listing, readiness, and guarded create/transition endpoints
per api.md contract.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


# =============================================================================
# Guard Schemas (T040)
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
# Task Create Schemas (T040)
# =============================================================================


class TaskCreateRequest(BaseModel):
    """Request body for task creation.

    Used for both preview and apply endpoints.
    """

    title: str
    type: str = Field(..., alias="type")
    session_id: str | None = Field(None, alias="sessionId")
    parent_id: str | None = Field(None, alias="parentId")
    depends_on: list[str] = Field(default_factory=list, alias="dependsOn")
    confirmed: bool = False

    model_config = {"populate_by_name": True}


class TaskPreview(BaseModel):
    """Preview of what task would be created."""

    title: str
    type: str
    session_id: str | None = Field(None, alias="sessionId")
    parent_id: str | None = Field(None, alias="parentId")
    depends_on: list[str] = Field(default_factory=list, alias="dependsOn")
    initial_state: str = Field("todo", alias="initialState")

    model_config = {"populate_by_name": True}


class TaskCreatePreviewResponse(BaseModel):
    """Response for task create preview endpoint.

    Returns validation result and preview of what would be created.
    """

    valid: bool
    guard_failures: list[GuardFailure] = Field(
        default_factory=list, alias="guardFailures"
    )
    guard_warnings: list[GuardWarning] = Field(
        default_factory=list, alias="guardWarnings"
    )
    preview: TaskPreview | None = None

    model_config = {"populate_by_name": True}


class TaskCreateResponse(BaseModel):
    """Response for task create (apply) endpoint."""

    task_id: str = Field(..., alias="taskId")
    audit_entry_id: str = Field(..., alias="auditEntryId")

    model_config = {"populate_by_name": True}


# =============================================================================
# Task Transition Schemas (T040)
# =============================================================================


class TaskTransitionRequest(BaseModel):
    """Request body for task state transition.

    Used for both preview and apply endpoints.
    """

    to_state: str = Field(..., alias="toState")
    confirmed: bool = False

    model_config = {"populate_by_name": True}


class TaskTransitionPreviewResponse(BaseModel):
    """Response for task transition preview endpoint."""

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


class TaskTransitionResponse(BaseModel):
    """Response for task transition (apply) endpoint."""

    task_id: str = Field(..., alias="taskId")
    previous_state: str = Field(..., alias="previousState")
    new_state: str = Field(..., alias="newState")
    audit_entry_id: str = Field(..., alias="auditEntryId")

    model_config = {"populate_by_name": True}


# =============================================================================
# Existing Schemas (T020/T022)
# =============================================================================


class BlockedByItem(BaseModel):
    """A single blocking dependency item.

    Represents a dependency that is blocking a task from being ready.
    """

    dependency_id: str = Field(..., alias="dependencyId")
    dependency_state: str | None = Field(None, alias="dependencyState")
    required_states: list[str] = Field(
        default_factory=lambda: ["done", "validated"], alias="requiredStates"
    )
    reason: str

    model_config = {"populate_by_name": True}


class GuardBlock(BaseModel):
    """A guard that is blocking an action.

    Represents a guard check that prevents a task from proceeding.
    """

    guard: str
    reason: str


class ValidationSummary(BaseModel):
    """Summary of validation status."""

    status: str  # needs_validation, in_progress, validated, rejected, unknown
    last_round: int | None = Field(None, alias="lastRound")
    validator_count: int = Field(0, alias="validatorCount")
    last_updated: str = Field(..., alias="lastUpdated")

    model_config = {"populate_by_name": True}


class TaskListItem(BaseModel):
    """A task in the list response.

    Contains all fields needed for task list views including readiness.
    """

    task_id: str = Field(..., alias="taskId")
    title: str
    state: str
    session_id: str | None = Field(None, alias="sessionId")
    parent_id: str | None = Field(None, alias="parentId")
    child_ids: list[str] = Field(default_factory=list, alias="childIds")
    depends_on: list[str] = Field(default_factory=list, alias="dependsOn")
    blocks_tasks: list[str] = Field(default_factory=list, alias="blocksTasks")
    validation_status: str = Field(..., alias="validationStatus")
    validation: ValidationSummary
    latest_verdict: str | None = Field(None, alias="latestVerdict")
    ready: bool
    blocked_by: list[BlockedByItem] = Field(default_factory=list, alias="blockedBy")
    created_at: str = Field(..., alias="createdAt")
    updated_at: str = Field(..., alias="updatedAt")

    model_config = {"populate_by_name": True}


class TaskListResponse(BaseModel):
    """Response for list tasks endpoint."""

    items: list[TaskListItem]
    total: int
    limit: int
    offset: int


class TaskReadinessResponse(BaseModel):
    """Response for task readiness endpoint.

    Contains computed readiness status with blocking information.
    """

    task_id: str = Field(..., alias="taskId")
    ready: bool
    blocked_by: list[BlockedByItem] = Field(default_factory=list, alias="blockedBy")
    guard_blocks: list[GuardBlock] = Field(default_factory=list, alias="guardBlocks")

    model_config = {"populate_by_name": True}
