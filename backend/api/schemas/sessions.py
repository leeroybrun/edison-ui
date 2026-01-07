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


# =============================================================================
# Session Context Schemas (T070)
# =============================================================================


class SessionContextResponse(BaseModel):
    """Response for GET /sessions/{sessionId}/context endpoint."""

    is_edison_project: bool = Field(..., alias="isEdisonProject")
    project_root: str = Field(..., alias="projectRoot")
    session_id: str = Field(..., alias="sessionId")
    session_state: str = Field(..., alias="sessionState")
    worktree_path: str | None = Field(None, alias="worktreePath")
    current_task_id: str | None = Field(None, alias="currentTaskId")
    current_task_state: str | None = Field(None, alias="currentTaskState")
    active_packs: list[str] = Field(default_factory=list, alias="activePacks")
    constitutions: dict[str, str] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


# =============================================================================
# Session Next Schemas (T070)
# =============================================================================


class SuggestedAction(BaseModel):
    """A suggested action from the next recommendation."""

    action_type: str = Field(..., alias="actionType")
    task_id: str | None = Field(None, alias="taskId")
    reason: str = ""

    model_config = {"populate_by_name": True}


class SessionNextResponse(BaseModel):
    """Response for GET /sessions/{sessionId}/next endpoint."""

    session_id: str = Field(..., alias="sessionId")
    recommendation: str
    suggested_actions: list[SuggestedAction] = Field(
        default_factory=list, alias="suggestedActions"
    )
    timestamp: str

    model_config = {"populate_by_name": True}
