"""Session-related Pydantic schemas (T021)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class SessionGitInfo(BaseModel):
    """Git information for a session."""

    branch_name: str | None = Field(None, alias="branchName")
    base_branch: str = Field(..., alias="baseBranch")

    model_config = {"populate_by_name": True}


class SessionListItem(BaseModel):
    """A session in the list response."""

    session_id: str = Field(..., alias="sessionId")
    state: str
    phase: str | None = None
    owner: str | None = None
    task_count: int = Field(0, alias="taskCount")
    created_at: str = Field(..., alias="createdAt")
    last_active_at: str | None = Field(None, alias="lastActiveAt")
    git: SessionGitInfo

    model_config = {"populate_by_name": True}


class SessionListResponse(BaseModel):
    """Response for list sessions endpoint."""

    items: list[SessionListItem]
    total: int
    limit: int
    offset: int
