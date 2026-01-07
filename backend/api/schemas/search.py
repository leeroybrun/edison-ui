"""Search-related Pydantic schemas (T074).

Implements schemas for search endpoints per api.md contract.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TaskSearchResult(BaseModel):
    """A task search result item."""

    task_id: str = Field(..., alias="taskId")
    title: str
    snippet: str
    score: float = Field(..., ge=0, le=1)
    project_id: str | None = Field(None, alias="projectId")

    model_config = {"populate_by_name": True}


class SessionSearchResult(BaseModel):
    """A session search result item."""

    session_id: str = Field(..., alias="sessionId")
    snippet: str
    score: float = Field(..., ge=0, le=1)
    project_id: str | None = Field(None, alias="projectId")

    model_config = {"populate_by_name": True}


class QASearchResult(BaseModel):
    """A QA search result item."""

    qa_id: str = Field(..., alias="qaId")
    task_id: str = Field(..., alias="taskId")
    snippet: str
    score: float = Field(..., ge=0, le=1)
    project_id: str | None = Field(None, alias="projectId")

    model_config = {"populate_by_name": True}


class MemorySearchResult(BaseModel):
    """A memory search result item."""

    provider_id: str = Field(..., alias="providerId")
    text: str
    score: float = Field(..., ge=0, le=1)
    meta: dict[str, str] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class SearchResults(BaseModel):
    """Container for search results across all scopes."""

    tasks: list[TaskSearchResult] = Field(default_factory=list)
    sessions: list[SessionSearchResult] = Field(default_factory=list)
    qa: list[QASearchResult] = Field(default_factory=list)
    memory: list[MemorySearchResult] = Field(default_factory=list)


class SearchResponse(BaseModel):
    """Response for search endpoints."""

    query: str
    results: SearchResults
    total_hits: int = Field(..., alias="totalHits")

    model_config = {"populate_by_name": True}
