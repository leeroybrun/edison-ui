"""Search endpoints (T074).

Implements search across tasks, sessions, QA, and memory scopes per api.md contracts.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from api.schemas.search import (
    MemorySearchResult,
    QASearchResult,
    SearchResponse,
    SearchResults,
    SessionSearchResult,
    TaskSearchResult,
)
from core.settings import get_settings
from services.project_discovery import ProjectDiscoveryService
from services.search_service import SearchService

# Project-scoped search router
project_router = APIRouter(prefix="/projects/{project_id}/search", tags=["search"])

# Global search router
global_router = APIRouter(prefix="/search", tags=["search"])


def get_discovery_service() -> ProjectDiscoveryService:
    """Get a configured project discovery service."""
    settings = get_settings()
    return ProjectDiscoveryService(
        scan_roots=settings.get_expanded_scan_roots(),
        ignore_patterns=settings.scan_ignore_patterns,
        pin_storage_path=settings.get_expanded_pin_storage_path(),
    )


def get_project_path(project_id: str) -> str:
    """Get the project path from project ID.

    Args:
        project_id: The project ID.

    Returns:
        The project path.

    Raises:
        HTTPException: If project not found.
    """
    service = get_discovery_service()
    project = service.get_project_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project.path


def parse_scopes(scope: str | None) -> list[str] | None:
    """Parse comma-separated scope string into list.

    Args:
        scope: Comma-separated scope string or None.

    Returns:
        List of scopes or None for all scopes.
    """
    if scope is None or scope.lower() == "all":
        return None

    scopes = [s.strip().lower() for s in scope.split(",") if s.strip()]
    return scopes if scopes else None


def convert_results_to_response(
    query: str,
    results: dict,
    project_id: str | None = None,
) -> SearchResponse:
    """Convert search service results to API response.

    Args:
        query: Original search query.
        results: Results from SearchService.search_all().
        project_id: Optional project ID to include in results.

    Returns:
        SearchResponse with formatted results.
    """
    tasks = [
        TaskSearchResult(
            task_id=r.entity_id,
            title=r.title or r.entity_id,
            snippet=r.snippet,
            score=r.score,
            project_id=project_id,
        )
        for r in results.get("tasks", [])
    ]

    sessions = [
        SessionSearchResult(
            session_id=r.entity_id,
            snippet=r.snippet,
            score=r.score,
            project_id=project_id,
        )
        for r in results.get("sessions", [])
    ]

    qa = [
        QASearchResult(
            qa_id=r.entity_id,
            task_id=r.metadata.get("task_id", ""),
            snippet=r.snippet,
            score=r.score,
            project_id=project_id,
        )
        for r in results.get("qa", [])
    ]

    memory = [
        MemorySearchResult(
            provider_id=r.metadata.get("provider_id", ""),
            text=r.snippet,
            score=r.score,
            meta=r.metadata.get("meta", {}),
        )
        for r in results.get("memory", [])
    ]

    search_results = SearchResults(
        tasks=tasks,
        sessions=sessions,
        qa=qa,
        memory=memory,
    )

    total_hits = len(tasks) + len(sessions) + len(qa) + len(memory)

    return SearchResponse(
        query=query,
        results=search_results,
        total_hits=total_hits,
    )


@project_router.get("", response_model=SearchResponse)
async def search_project(
    project_id: str,
    q: Annotated[str, Query(description="Search query")],
    scope: Annotated[
        str | None,
        Query(description="Comma-separated scopes: tasks,sessions,qa,memory"),
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Max items per scope")
    ] = 20,
) -> SearchResponse:
    """Search across entities within a project.

    Searches tasks, sessions, QA records, and memory (when configured)
    using text matching. Results are scored by relevance.
    """
    project_path = get_project_path(project_id)
    search_service = SearchService(project_path)

    scopes = parse_scopes(scope)
    results = search_service.search_all(q, scopes=scopes, limit=limit)

    return convert_results_to_response(q, results, project_id=project_id)


@global_router.get("", response_model=SearchResponse)
async def search_global(
    q: Annotated[str, Query(description="Search query")],
    project_id: Annotated[
        str | None,
        Query(alias="projectId", description="Filter to specific project"),
    ] = None,
    scope: Annotated[
        str | None,
        Query(description="Comma-separated scopes: tasks,sessions,qa,memory"),
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Max items per scope")
    ] = 20,
) -> SearchResponse:
    """Global search across all projects.

    If projectId is provided, searches only that project.
    Otherwise, searches across all discovered projects.
    """
    discovery_service = get_discovery_service()
    scopes = parse_scopes(scope)

    # If project_id specified, search only that project
    if project_id:
        project = discovery_service.get_project_by_id(project_id)
        if project is None:
            raise HTTPException(
                status_code=404, detail=f"Project {project_id} not found"
            )

        search_service = SearchService(project.path)
        results = search_service.search_all(q, scopes=scopes, limit=limit)
        return convert_results_to_response(q, results, project_id=project_id)

    # Search across all projects
    all_results: dict[str, list] = {
        "tasks": [],
        "sessions": [],
        "qa": [],
        "memory": [],
    }

    projects = discovery_service.discover_projects()
    for project in projects:
        search_service = SearchService(project.path)
        project_results = search_service.search_all(q, scopes=scopes, limit=limit)

        # Add project ID to each result
        for scope_name in all_results:
            for result in project_results.get(scope_name, []):
                result.metadata["project_id"] = project.project_id
                all_results[scope_name].append(result)

    # Sort each scope by score and limit
    for scope_name in all_results:
        all_results[scope_name].sort(key=lambda x: x.score, reverse=True)
        all_results[scope_name] = all_results[scope_name][:limit]

    # Convert to response with project IDs
    tasks = [
        TaskSearchResult(
            task_id=r.entity_id,
            title=r.title or r.entity_id,
            snippet=r.snippet,
            score=r.score,
            project_id=r.metadata.get("project_id"),
        )
        for r in all_results.get("tasks", [])
    ]

    sessions = [
        SessionSearchResult(
            session_id=r.entity_id,
            snippet=r.snippet,
            score=r.score,
            project_id=r.metadata.get("project_id"),
        )
        for r in all_results.get("sessions", [])
    ]

    qa = [
        QASearchResult(
            qa_id=r.entity_id,
            task_id=r.metadata.get("task_id", ""),
            snippet=r.snippet,
            score=r.score,
            project_id=r.metadata.get("project_id"),
        )
        for r in all_results.get("qa", [])
    ]

    memory = [
        MemorySearchResult(
            provider_id=r.metadata.get("provider_id", ""),
            text=r.snippet,
            score=r.score,
            meta=r.metadata.get("meta", {}),
        )
        for r in all_results.get("memory", [])
    ]

    search_results = SearchResults(
        tasks=tasks,
        sessions=sessions,
        qa=qa,
        memory=memory,
    )

    total_hits = len(tasks) + len(sessions) + len(qa) + len(memory)

    return SearchResponse(
        query=q,
        results=search_results,
        total_hits=total_hits,
    )
