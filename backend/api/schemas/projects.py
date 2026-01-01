"""Project-related Pydantic schemas (T010)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ProjectHealth(BaseModel):
    """Health counts for a project."""

    task_count: int = Field(..., alias="taskCount")
    session_count: int = Field(..., alias="sessionCount")
    qa_count: int = Field(..., alias="qaCount")
    active_count: int = Field(..., alias="activeCount")

    model_config = {"populate_by_name": True}


class ProjectListItem(BaseModel):
    """A project in the list response."""

    project_id: str = Field(..., alias="projectId")
    path: str
    name: str
    pinned: bool
    health: ProjectHealth
    last_activity_at: str | None = Field(None, alias="lastActivityAt")
    has_git: bool = Field(..., alias="hasGit")
    errors: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class ProjectListResponse(BaseModel):
    """Response for list projects endpoint."""

    items: list[ProjectListItem]
    total: int
    limit: int
    offset: int


class ProjectConfig(BaseModel):
    """Project configuration section."""

    scan_roots: list[str] = Field(..., alias="scanRoots")
    memory_enabled: bool = Field(False, alias="memoryEnabled")

    model_config = {"populate_by_name": True}


class ProjectDetail(BaseModel):
    """Full project detail response."""

    project_id: str = Field(..., alias="projectId")
    path: str
    name: str
    pinned: bool
    health: ProjectHealth
    last_activity_at: str | None = Field(None, alias="lastActivityAt")
    has_git: bool = Field(..., alias="hasGit")
    errors: list[str] = Field(default_factory=list)
    config: ProjectConfig

    model_config = {"populate_by_name": True}


class PinRequest(BaseModel):
    """Request body for pin/unpin endpoint."""

    pinned: bool


class PinResponse(BaseModel):
    """Response for pin/unpin endpoint."""

    project_id: str = Field(..., alias="projectId")
    pinned: bool

    model_config = {"populate_by_name": True}
