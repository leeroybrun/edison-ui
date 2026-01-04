"""Task-related Pydantic schemas (T020/T022).

Implements schemas for task listing and readiness endpoints per api.md contract.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


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
