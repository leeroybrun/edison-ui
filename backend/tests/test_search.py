"""Tests for search endpoints (T074).

RED Phase: These tests MUST fail initially as the endpoints don't exist yet.

Implements tests for:
- GET /projects/{projectId}/search - Search within a project
- GET /search - Global search across all projects
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import create_app


def create_task_frontmatter(
    task_id: str, title: str, state: str = "todo", body: str = ""
) -> str:
    """Create task markdown with frontmatter."""
    return f"""---
id: {task_id}
title: {title}
state: {state}
created_at: '2025-01-01T10:00:00Z'
updated_at: '2025-01-01T10:00:00Z'
---
# {title}

{body}
"""


def create_qa_frontmatter(
    task_id: str,
    qa_id: str,
    state: str = "todo",
    verdict: str | None = None,
) -> str:
    """Create QA file frontmatter."""
    lines = [
        "---",
        f"id: {qa_id}",
        f"task_id: {task_id}",
        f"state: {state}",
    ]
    if verdict:
        lines.append(f"verdict: {verdict}")
    lines.append("created_at: '2025-01-01T10:00:00Z'")
    lines.append("updated_at: '2025-01-01T10:00:00Z'")
    lines.append("---")
    return "\n".join(lines)


def create_session_json(
    session_id: str, owner: str = "test-user", task_count: int = 0
) -> dict:
    """Create session.json content."""
    return {
        "id": session_id,
        "meta": {
            "owner": owner,
            "createdAt": "2025-01-01T10:00:00Z",
            "lastActive": "2025-01-01T12:00:00Z",
        },
        "phase": "implementation",
        "git": {"branchName": f"session/{session_id}", "baseBranch": "main"},
        "tasks": {},
    }


@pytest.fixture
def mock_edison_project_with_searchable_content(tmp_path: Path) -> Path:
    """Create a mock Edison project with searchable content across scopes."""
    project_path = tmp_path / "test-project"
    project_path.mkdir()
    (project_path / ".edison").mkdir()
    (project_path / ".git").mkdir()  # Required for project discovery

    project_dir = project_path / ".project"
    project_dir.mkdir()

    # Create tasks directory structure
    tasks_dir = project_dir / "tasks"
    tasks_dir.mkdir()
    for state in ["todo", "wip", "done", "validated"]:
        (tasks_dir / state).mkdir()

    # T001: Authentication task - should match "auth" search
    (tasks_dir / "wip" / "T001.md").write_text(
        create_task_frontmatter(
            "T001",
            "Implement authentication flow",
            state="wip",
            body="This task implements OAuth2 authentication using JWT tokens.",
        )
    )

    # T002: Database task - should match "database" search
    (tasks_dir / "done" / "T002.md").write_text(
        create_task_frontmatter(
            "T002",
            "Design database schema",
            state="done",
            body="Create PostgreSQL database schema for user management.",
        )
    )

    # T003: API task - should match "api" search
    (tasks_dir / "todo" / "T003.md").write_text(
        create_task_frontmatter(
            "T003",
            "Build REST API endpoints",
            state="todo",
            body="Implement API endpoints for user CRUD operations.",
        )
    )

    # T004: Also matches "auth" - for score testing
    (tasks_dir / "todo" / "T004.md").write_text(
        create_task_frontmatter(
            "T004",
            "Add two-factor authentication",
            state="todo",
            body="Implement 2FA using TOTP for additional security.",
        )
    )

    # Create sessions
    sessions_dir = project_dir / "sessions"
    sessions_dir.mkdir()
    (sessions_dir / "active").mkdir()
    (sessions_dir / "done").mkdir()

    # Session with auth-related activity
    session_1_dir = sessions_dir / "active" / "session-auth-impl"
    session_1_dir.mkdir(parents=True)
    session_1_json = create_session_json("session-auth-impl", owner="auth-dev")
    session_1_json["activity"] = [
        {"type": "task.claim", "taskId": "T001", "message": "Started auth work"},
        {"type": "commit", "message": "Add OAuth2 authentication flow"},
    ]
    (session_1_dir / "session.json").write_text(json.dumps(session_1_json, indent=2))

    # Session with database work
    session_2_dir = sessions_dir / "done" / "session-db-setup"
    session_2_dir.mkdir(parents=True)
    session_2_json = create_session_json("session-db-setup", owner="db-dev")
    session_2_json["activity"] = [
        {"type": "task.done", "taskId": "T002", "message": "Completed DB schema"},
    ]
    (session_2_dir / "session.json").write_text(json.dumps(session_2_json, indent=2))

    # Create QA records
    qa_dir = project_dir / "qa"
    qa_dir.mkdir()
    for state in ["todo", "wip", "done", "validated"]:
        (qa_dir / state).mkdir()

    # QA for T002 - completed validation
    (qa_dir / "done" / "T002-qa.md").write_text(
        create_qa_frontmatter("T002", "QA-T002", state="done", verdict="pass")
        + "\n# QA T002\nDatabase schema validation passed. Auth integration verified."
    )

    # QA for T001 - in progress
    (qa_dir / "wip" / "T001-qa.md").write_text(
        create_qa_frontmatter("T001", "QA-T001", state="wip")
        + "\n# QA T001\nValidating authentication implementation."
    )

    return project_path


@pytest.fixture
def app_with_searchable_content(
    mock_edison_project_with_searchable_content: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    """Create app with mocked scan roots containing searchable content."""
    monkeypatch.setenv(
        "SCAN_ROOTS", str(mock_edison_project_with_searchable_content.parent)
    )
    monkeypatch.setenv("PIN_STORAGE_PATH", str(tmp_path / "pins.json"))

    from core.settings import get_settings

    get_settings.cache_clear()

    app = create_app()
    return TestClient(app)


@pytest.fixture
def project_id(app_with_searchable_content: TestClient) -> str:
    """Get the project ID."""
    response = app_with_searchable_content.get("/api/v1/projects")
    return str(response.json()["items"][0]["projectId"])


# =============================================================================
# Tests for GET /projects/{projectId}/search
# =============================================================================


class TestProjectSearch:
    """Tests for project-scoped search endpoint."""

    def test_search_requires_query_parameter(
        self, app_with_searchable_content: TestClient, project_id: str
    ) -> None:
        """Should return 422 if q parameter is missing."""
        response = app_with_searchable_content.get(
            f"/api/v1/projects/{project_id}/search"
        )
        assert response.status_code == 422

    def test_search_returns_200_with_results(
        self, app_with_searchable_content: TestClient, project_id: str
    ) -> None:
        """Should return 200 OK with search results."""
        response = app_with_searchable_content.get(
            f"/api/v1/projects/{project_id}/search?q=authentication"
        )
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert data["query"] == "authentication"
        assert "results" in data
        assert "totalHits" in data

    def test_search_returns_matching_tasks(
        self, app_with_searchable_content: TestClient, project_id: str
    ) -> None:
        """Should return tasks matching the query in title or body."""
        response = app_with_searchable_content.get(
            f"/api/v1/projects/{project_id}/search?q=authentication"
        )
        data = response.json()
        tasks = data["results"]["tasks"]
        assert len(tasks) >= 1
        # T001 should match "authentication" in title
        task_ids = [t["taskId"] for t in tasks]
        assert "T001" in task_ids

    def test_search_task_result_format(
        self, app_with_searchable_content: TestClient, project_id: str
    ) -> None:
        """Task results should have correct format per API contract."""
        response = app_with_searchable_content.get(
            f"/api/v1/projects/{project_id}/search?q=authentication"
        )
        data = response.json()
        tasks = data["results"]["tasks"]
        assert len(tasks) >= 1
        task = tasks[0]
        assert "taskId" in task
        assert "title" in task
        assert "snippet" in task
        assert "score" in task
        assert 0 <= task["score"] <= 1

    def test_search_returns_matching_sessions(
        self, app_with_searchable_content: TestClient, project_id: str
    ) -> None:
        """Should return sessions matching the query."""
        response = app_with_searchable_content.get(
            f"/api/v1/projects/{project_id}/search?q=auth"
        )
        data = response.json()
        sessions = data["results"]["sessions"]
        # Should find session-auth-impl
        session_ids = [s["sessionId"] for s in sessions]
        assert "session-auth-impl" in session_ids

    def test_search_session_result_format(
        self, app_with_searchable_content: TestClient, project_id: str
    ) -> None:
        """Session results should have correct format."""
        response = app_with_searchable_content.get(
            f"/api/v1/projects/{project_id}/search?q=auth"
        )
        data = response.json()
        sessions = data["results"]["sessions"]
        if sessions:
            session = sessions[0]
            assert "sessionId" in session
            assert "snippet" in session
            assert "score" in session
            assert 0 <= session["score"] <= 1

    def test_search_returns_matching_qa(
        self, app_with_searchable_content: TestClient, project_id: str
    ) -> None:
        """Should return QA records matching the query."""
        response = app_with_searchable_content.get(
            f"/api/v1/projects/{project_id}/search?q=authentication"
        )
        data = response.json()
        qa_results = data["results"]["qa"]
        # Should find QA-T001 which mentions authentication
        qa_ids = [q["qaId"] for q in qa_results]
        assert "QA-T001" in qa_ids

    def test_search_qa_result_format(
        self, app_with_searchable_content: TestClient, project_id: str
    ) -> None:
        """QA results should have correct format."""
        response = app_with_searchable_content.get(
            f"/api/v1/projects/{project_id}/search?q=authentication"
        )
        data = response.json()
        qa_results = data["results"]["qa"]
        if qa_results:
            qa = qa_results[0]
            assert "qaId" in qa
            assert "taskId" in qa
            assert "snippet" in qa
            assert "score" in qa

    def test_search_memory_returns_empty_when_not_configured(
        self, app_with_searchable_content: TestClient, project_id: str
    ) -> None:
        """Memory search should return empty array if not configured."""
        response = app_with_searchable_content.get(
            f"/api/v1/projects/{project_id}/search?q=anything"
        )
        data = response.json()
        assert "memory" in data["results"]
        assert isinstance(data["results"]["memory"], list)

    def test_search_scope_filter_tasks_only(
        self, app_with_searchable_content: TestClient, project_id: str
    ) -> None:
        """Should only search tasks when scope=tasks."""
        response = app_with_searchable_content.get(
            f"/api/v1/projects/{project_id}/search?q=auth&scope=tasks"
        )
        data = response.json()
        assert "tasks" in data["results"]
        assert data["results"]["sessions"] == []
        assert data["results"]["qa"] == []
        assert data["results"]["memory"] == []

    def test_search_scope_multiple_scopes(
        self, app_with_searchable_content: TestClient, project_id: str
    ) -> None:
        """Should search multiple scopes when comma-separated."""
        response = app_with_searchable_content.get(
            f"/api/v1/projects/{project_id}/search?q=auth&scope=tasks,sessions"
        )
        data = response.json()
        # Should have tasks and sessions, but empty qa and memory
        assert "tasks" in data["results"]
        assert "sessions" in data["results"]
        assert data["results"]["qa"] == []
        assert data["results"]["memory"] == []

    def test_search_limit_parameter(
        self, app_with_searchable_content: TestClient, project_id: str
    ) -> None:
        """Should respect limit parameter per scope."""
        response = app_with_searchable_content.get(
            f"/api/v1/projects/{project_id}/search?q=auth&limit=1"
        )
        data = response.json()
        # Should have at most 1 result per scope
        assert len(data["results"]["tasks"]) <= 1

    def test_search_total_hits_counts_all_matches(
        self, app_with_searchable_content: TestClient, project_id: str
    ) -> None:
        """totalHits should count all matches across scopes."""
        response = app_with_searchable_content.get(
            f"/api/v1/projects/{project_id}/search?q=auth"
        )
        data = response.json()
        # Count actual results
        total = (
            len(data["results"]["tasks"])
            + len(data["results"]["sessions"])
            + len(data["results"]["qa"])
            + len(data["results"]["memory"])
        )
        assert data["totalHits"] == total

    def test_search_project_not_found(
        self, app_with_searchable_content: TestClient
    ) -> None:
        """Should return 404 for non-existent project."""
        response = app_with_searchable_content.get(
            "/api/v1/projects/nonexistent-project/search?q=test"
        )
        assert response.status_code == 404


# =============================================================================
# Tests for GET /search (Global Search)
# =============================================================================


class TestGlobalSearch:
    """Tests for global search endpoint."""

    def test_global_search_requires_query_parameter(
        self, app_with_searchable_content: TestClient
    ) -> None:
        """Should return 422 if q parameter is missing."""
        response = app_with_searchable_content.get("/api/v1/search")
        assert response.status_code == 422

    def test_global_search_returns_200(
        self, app_with_searchable_content: TestClient
    ) -> None:
        """Should return 200 OK with search results."""
        response = app_with_searchable_content.get("/api/v1/search?q=authentication")
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert "totalHits" in data

    def test_global_search_filter_by_project(
        self, app_with_searchable_content: TestClient, project_id: str
    ) -> None:
        """Should filter results to specific project when projectId provided."""
        response = app_with_searchable_content.get(
            f"/api/v1/search?q=authentication&projectId={project_id}"
        )
        assert response.status_code == 200
        data = response.json()
        # All results should be from the specified project
        for task in data["results"]["tasks"]:
            assert task.get("projectId") == project_id

    def test_global_search_scope_filter(
        self, app_with_searchable_content: TestClient
    ) -> None:
        """Should respect scope filter in global search."""
        response = app_with_searchable_content.get(
            "/api/v1/search?q=auth&scope=tasks"
        )
        data = response.json()
        assert data["results"]["sessions"] == []
        assert data["results"]["qa"] == []
        assert data["results"]["memory"] == []

    def test_global_search_limit_parameter(
        self, app_with_searchable_content: TestClient
    ) -> None:
        """Should respect limit parameter in global search."""
        response = app_with_searchable_content.get(
            "/api/v1/search?q=auth&limit=1"
        )
        data = response.json()
        assert len(data["results"]["tasks"]) <= 1


# =============================================================================
# Tests for Search Scoring
# =============================================================================


class TestSearchScoring:
    """Tests for search result scoring."""

    def test_title_matches_score_higher_than_body(
        self, app_with_searchable_content: TestClient, project_id: str
    ) -> None:
        """Tasks with query match in title should score higher than body-only match."""
        response = app_with_searchable_content.get(
            f"/api/v1/projects/{project_id}/search?q=authentication"
        )
        data = response.json()
        tasks = data["results"]["tasks"]
        if len(tasks) >= 2:
            # T001 has "authentication" in title, should score higher
            scores_by_id = {t["taskId"]: t["score"] for t in tasks}
            # T001 should have a high score since it matches title
            assert scores_by_id.get("T001", 0) > 0.5

    def test_scores_are_normalized(
        self, app_with_searchable_content: TestClient, project_id: str
    ) -> None:
        """All scores should be between 0 and 1."""
        response = app_with_searchable_content.get(
            f"/api/v1/projects/{project_id}/search?q=auth"
        )
        data = response.json()
        for scope in ["tasks", "sessions", "qa", "memory"]:
            for result in data["results"].get(scope, []):
                assert 0 <= result["score"] <= 1, f"Score out of range in {scope}"


# =============================================================================
# Tests for Search Snippets
# =============================================================================


class TestSearchSnippets:
    """Tests for search result snippets."""

    def test_snippet_contains_match_context(
        self, app_with_searchable_content: TestClient, project_id: str
    ) -> None:
        """Snippets should contain context around the matched term."""
        response = app_with_searchable_content.get(
            f"/api/v1/projects/{project_id}/search?q=OAuth2"
        )
        data = response.json()
        tasks = data["results"]["tasks"]
        for task in tasks:
            if task["taskId"] == "T001":
                # Snippet should contain matched term or context
                assert "OAuth2" in task["snippet"] or "authentication" in task["snippet"].lower()

    def test_snippet_truncated_for_long_content(
        self, app_with_searchable_content: TestClient, project_id: str
    ) -> None:
        """Snippets should be reasonably short."""
        response = app_with_searchable_content.get(
            f"/api/v1/projects/{project_id}/search?q=database"
        )
        data = response.json()
        for scope in ["tasks", "sessions", "qa"]:
            for result in data["results"].get(scope, []):
                # Snippets should not be excessively long
                assert len(result["snippet"]) <= 300
