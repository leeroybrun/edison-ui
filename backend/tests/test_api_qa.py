"""Tests for QA endpoints (T030).

RED Phase: These tests MUST fail initially as the endpoints don't exist yet.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import create_app


def create_task_frontmatter(task_id: str, title: str) -> str:
    """Create minimal task frontmatter."""
    return f"""---\n{task_id}
{title}
state: done
created_at: '2025-01-01T10:00:00Z'
updated_at: '2025-01-01T10:00:00Z'
---"""


def create_qa_frontmatter(
    task_id: str,
    qa_id: str,
    state: str = "todo",
    verdict: str | None = None,
    session_id: str | None = None,
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
    if session_id:
        lines.append(f"session_id: {session_id}")
    lines.append("created_at: '2025-01-01T10:00:00Z'")
    lines.append("updated_at: '2025-01-01T10:00:00Z'")
    lines.append("---")
    return "\n".join(lines)


@pytest.fixture
def mock_edison_project_with_qa(tmp_path: Path) -> Path:
    """Create a mock Edison project with tasks and QA records."""
    project_path = tmp_path / "test-project"
    project_path.mkdir()
    (project_path / ".edison").mkdir()

    project_dir = project_path / ".project"
    project_dir.mkdir()

    # Create tasks
    tasks_dir = project_dir / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "done").mkdir()
    (tasks_dir / "validated").mkdir()

    # T001: Has QA in TODO state
    (tasks_dir / "done" / "T001.md").write_text(
        create_task_frontmatter("T001", "Task 1")
    )

    # T002: Has QA in DONE state with PASS verdict
    (tasks_dir / "done" / "T002.md").write_text(
        create_task_frontmatter("T002", "Task 2")
    )

    # T003: Has QA in WIP state
    (tasks_dir / "done" / "T003.md").write_text(
        create_task_frontmatter("T003", "Task 3")
    )

    # Create QA records
    qa_dir = project_dir / "qa"
    qa_dir.mkdir()
    for state in ["todo", "wip", "done", "validated"]:
        (qa_dir / state).mkdir()

    # QA-T001: TODO
    (qa_dir / "todo" / "T001-qa.md").write_text(
        create_qa_frontmatter("T001", "QA-T001", state="todo")
        + "\n# QA T001\nPending validation."
    )

    # QA-T002: DONE (Pass)
    (qa_dir / "done" / "T002-qa.md").write_text(
        create_qa_frontmatter("T002", "QA-T002", state="done", verdict="pass")
        + "\n# QA T002\nValidation passed."
    )

    # QA-T003: WIP (Session scoped)
    (qa_dir / "wip" / "T003-qa.md").write_text(
        create_qa_frontmatter("T003", "QA-T003", state="wip", session_id="session-123")
        + "\n# QA T003\nValidation in progress."
    )

    # Create Evidence for T002
    evidence_dir = qa_dir / "validation-evidence" / "T002" / "round-1"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "test-output.txt").write_text("All tests passed.")
    (evidence_dir / "coverage.txt").write_text("Coverage: 100%")

    # Create marker files for evidence
    (evidence_dir / "context7-react.txt").write_text("React context used")

    return project_path


@pytest.fixture
def app_with_qa(
    mock_edison_project_with_qa: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    """Create app with mocked scan roots."""
    monkeypatch.setenv("SCAN_ROOTS", str(mock_edison_project_with_qa.parent))
    monkeypatch.setenv("PIN_STORAGE_PATH", str(tmp_path / "pins.json"))

    from core.settings import get_settings

    get_settings.cache_clear()

    app = create_app()
    return TestClient(app)


@pytest.fixture
def project_id(app_with_qa: TestClient) -> str:
    """Get the project ID."""
    response = app_with_qa.get("/api/v1/projects")
    return str(response.json()["items"][0]["projectId"])


class TestListQARecords:
    """Tests for GET /projects/{projectId}/qa endpoint."""

    def test_list_qa_returns_200(
        self, app_with_qa: TestClient, project_id: str
    ) -> None:
        """Should return 200 OK with list of QA records."""
        response = app_with_qa.get(f"/api/v1/projects/{project_id}/qa")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 3

    def test_list_qa_filter_by_state(
        self, app_with_qa: TestClient, project_id: str
    ) -> None:
        """Should filter QA records by state."""
        response = app_with_qa.get(f"/api/v1/projects/{project_id}/qa?state=todo")
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["taskId"] == "T001"

    def test_list_qa_filter_by_verdict(
        self, app_with_qa: TestClient, project_id: str
    ) -> None:
        """Should filter QA records by verdict."""
        response = app_with_qa.get(f"/api/v1/projects/{project_id}/qa?verdict=pass")
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["taskId"] == "T002"

    def test_list_qa_filter_by_session(
        self, app_with_qa: TestClient, project_id: str
    ) -> None:
        """Should filter QA records by session ID."""
        response = app_with_qa.get(
            f"/api/v1/projects/{project_id}/qa?sessionId=session-123"
        )
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["taskId"] == "T003"


class TestGetQADetail:
    """Tests for GET /projects/{projectId}/tasks/{taskId}/qa endpoint."""

    def test_get_qa_detail_returns_200(
        self, app_with_qa: TestClient, project_id: str
    ) -> None:
        """Should return 200 OK with QA detail."""
        response = app_with_qa.get(f"/api/v1/projects/{project_id}/tasks/T002/qa")
        assert response.status_code == 200
        data = response.json()
        assert data["taskId"] == "T002"
        assert data["state"] == "done"
        assert data["verdict"] == "pass"

    def test_get_qa_detail_includes_evidence(
        self, app_with_qa: TestClient, project_id: str
    ) -> None:
        """Should include evidence rounds and artifacts."""
        response = app_with_qa.get(f"/api/v1/projects/{project_id}/tasks/T002/qa")
        data = response.json()
        assert "rounds" in data
        assert len(data["rounds"]) == 1
        round_1 = data["rounds"][0]
        assert round_1["roundNumber"] == 1
        assert "artifacts" in round_1
        artifacts = [a["name"] for a in round_1["artifacts"]]
        assert "test-output.txt" in artifacts
        assert "coverage.txt" in artifacts
        assert "context7-react.txt" in artifacts

    def test_get_qa_detail_404_if_no_record(
        self, app_with_qa: TestClient, project_id: str
    ) -> None:
        """Should return 404 if no QA record exists."""
        response = app_with_qa.get(f"/api/v1/projects/{project_id}/tasks/UNKNOWN/qa")
        assert response.status_code == 404
