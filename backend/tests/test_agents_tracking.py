"""Tests for agent tracking endpoints (T072).

RED Phase: These tests MUST fail initially as the endpoints don't exist yet.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.fixture
def mock_edison_project_with_process_events(tmp_path: Path) -> Path:
    """Create a mock Edison project with process events JSONL."""
    project_path = tmp_path / "test-project"
    project_path.mkdir()

    # Create .edison directory (marks it as an Edison project)
    edison_dir = project_path / ".edison"
    edison_dir.mkdir()

    # Create .project directory
    project_dir = project_path / ".project"
    project_dir.mkdir()

    # Create logs/edison directory
    logs_dir = project_dir / "logs" / "edison"
    logs_dir.mkdir(parents=True)

    # Create process-events.jsonl with sample events
    now = datetime.now(timezone.utc)
    events = [
        # Active validation agent (started, has heartbeats, no completion)
        {
            "ts": (now - timedelta(minutes=5)).isoformat(),
            "event": "started",
            "runId": "run-validation-1",
            "pid": 12345,
            "hostname": "localhost",
            "kind": "validation",
            "taskId": "T001",
            "sessionId": "session-1",
            "validatorId": "code-review",
            "round": 2,
            "model": "claude-3-5-sonnet",
        },
        {
            "ts": (now - timedelta(minutes=2)).isoformat(),
            "event": "heartbeat",
            "runId": "run-validation-1",
            "pid": 12345,
        },
        # Active implementation agent
        {
            "ts": (now - timedelta(minutes=10)).isoformat(),
            "event": "started",
            "runId": "run-impl-1",
            "pid": 23456,
            "hostname": "localhost",
            "kind": "implementation",
            "taskId": "T002",
            "sessionId": "session-1",
            "model": "claude-3-5-sonnet",
        },
        {
            "ts": (now - timedelta(minutes=1)).isoformat(),
            "event": "heartbeat",
            "runId": "run-impl-1",
            "pid": 23456,
        },
        # Completed orchestrator
        {
            "ts": (now - timedelta(hours=1)).isoformat(),
            "event": "started",
            "runId": "run-orch-1",
            "pid": 11111,
            "hostname": "localhost",
            "kind": "orchestrator",
            "sessionId": "session-1",
        },
        {
            "ts": (now - timedelta(minutes=45)).isoformat(),
            "event": "completed",
            "runId": "run-orch-1",
            "pid": 11111,
        },
        # Stale agent (no recent heartbeat)
        {
            "ts": (now - timedelta(minutes=10)).isoformat(),
            "event": "started",
            "runId": "run-stale-1",
            "pid": 99999,
            "hostname": "localhost",
            "kind": "validation",
            "taskId": "T003",
            "sessionId": "session-2",
            "validatorId": "security",
            "round": 1,
        },
        # No heartbeat, so this should be stale (>120s default threshold)
    ]

    jsonl_content = "\n".join(json.dumps(e) for e in events)
    (logs_dir / "process-events.jsonl").write_text(jsonl_content)

    # Create .git directory (marks it as a git repo)
    git_dir = project_path / ".git"
    git_dir.mkdir()

    return project_path


@pytest.fixture
def mock_edison_project_empty_events(tmp_path: Path) -> Path:
    """Create a mock Edison project with no process events."""
    project_path = tmp_path / "empty-project"
    project_path.mkdir()

    # Create .edison directory
    edison_dir = project_path / ".edison"
    edison_dir.mkdir()

    # Create .project directory (no logs)
    project_dir = project_path / ".project"
    project_dir.mkdir()

    # Create .git directory
    git_dir = project_path / ".git"
    git_dir.mkdir()

    return project_path


@pytest.fixture
def app_with_process_events(
    mock_edison_project_with_process_events: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    """Create app with mocked scan roots for process events tests."""
    scan_root = mock_edison_project_with_process_events.parent
    monkeypatch.setenv("SCAN_ROOTS", str(scan_root))
    monkeypatch.setenv("PIN_STORAGE_PATH", str(tmp_path / "pins.json"))

    # Clear settings cache to pick up new env
    from core.settings import get_settings

    get_settings.cache_clear()

    app = create_app()
    return TestClient(app)


@pytest.fixture
def app_with_empty_events(
    mock_edison_project_empty_events: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    """Create app for empty events tests."""
    scan_root = mock_edison_project_empty_events.parent
    monkeypatch.setenv("SCAN_ROOTS", str(scan_root))
    monkeypatch.setenv("PIN_STORAGE_PATH", str(tmp_path / "pins.json"))

    from core.settings import get_settings

    get_settings.cache_clear()

    app = create_app()
    return TestClient(app)


@pytest.fixture
def project_id(app_with_process_events: TestClient) -> str:
    """Get the project ID from the discovered project."""
    response = app_with_process_events.get("/api/v1/projects")
    return str(response.json()["items"][0]["projectId"])


@pytest.fixture
def empty_project_id(app_with_empty_events: TestClient) -> str:
    """Get the project ID for empty events project."""
    response = app_with_empty_events.get("/api/v1/projects")
    return str(response.json()["items"][0]["projectId"])


# =============================================================================
# GET /projects/{projectId}/agents/active Tests
# =============================================================================


class TestListActiveAgents:
    """Tests for GET /projects/{projectId}/agents/active endpoint."""

    def test_returns_200(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should return 200 OK."""
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/active"
        )
        assert response.status_code == 200

    def test_returns_items_array(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should return items array in response."""
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/active"
        )
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_returns_total_count(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should return total count."""
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/active"
        )
        data = response.json()
        assert "total" in data
        assert isinstance(data["total"], int)

    def test_excludes_completed_agents(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should exclude agents that have completed."""
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/active"
        )
        data = response.json()

        run_ids = [item["runId"] for item in data["items"]]
        # Completed orchestrator should not appear
        assert "run-orch-1" not in run_ids

    def test_includes_running_agents(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should include agents that are still running."""
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/active"
        )
        data = response.json()

        run_ids = [item["runId"] for item in data["items"]]
        assert "run-validation-1" in run_ids
        assert "run-impl-1" in run_ids

    def test_agent_has_required_fields(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should include all required fields for each agent."""
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/active"
        )
        data = response.json()

        required_fields = [
            "runId",
            "type",
            "taskId",
            "sessionId",
            "processId",
            "hostname",
            "startedAt",
            "lastActiveAt",
            "isRunning",
            "isStale",
            "state",
        ]

        for item in data["items"]:
            for field in required_fields:
                assert field in item, f"Missing field: {field}"

    def test_validation_agent_has_validator_fields(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should include validatorId and round for validation agents."""
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/active"
        )
        data = response.json()

        validation_agent = next(
            (item for item in data["items"] if item["runId"] == "run-validation-1"),
            None,
        )
        assert validation_agent is not None
        assert validation_agent["validatorId"] == "code-review"
        assert validation_agent["round"] == 2

    def test_filter_by_session_id(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should filter by sessionId."""
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/active?sessionId=session-1"
        )
        data = response.json()

        for item in data["items"]:
            assert item["sessionId"] == "session-1"

    def test_filter_by_task_id(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should filter by taskId."""
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/active?taskId=T001"
        )
        data = response.json()

        for item in data["items"]:
            assert item["taskId"] == "T001"

    def test_filter_by_type(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should filter by type."""
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/active?type=validation"
        )
        data = response.json()

        for item in data["items"]:
            assert item["type"] == "validation"

    def test_identifies_stale_agents(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should identify stale agents (no heartbeat within threshold)."""
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/active"
        )
        data = response.json()

        stale_agent = next(
            (item for item in data["items"] if item["runId"] == "run-stale-1"),
            None,
        )
        # Stale agent may or may not appear in active list depending on impl
        # If it appears, it should be marked stale
        if stale_agent:
            assert stale_agent["isStale"] is True

    def test_returns_404_for_unknown_project(
        self, app_with_process_events: TestClient
    ) -> None:
        """Should return 404 for unknown project."""
        response = app_with_process_events.get(
            "/api/v1/projects/unknown-project-id/agents/active"
        )
        assert response.status_code == 404

    def test_returns_empty_for_no_events(
        self, app_with_empty_events: TestClient, empty_project_id: str
    ) -> None:
        """Should return empty list when no events exist."""
        response = app_with_empty_events.get(
            f"/api/v1/projects/{empty_project_id}/agents/active"
        )
        data = response.json()

        assert data["items"] == []
        assert data["total"] == 0


# =============================================================================
# GET /projects/{projectId}/agents/processes Tests
# =============================================================================


class TestListProcesses:
    """Tests for GET /projects/{projectId}/agents/processes endpoint."""

    def test_returns_200(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should return 200 OK."""
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/processes"
        )
        assert response.status_code == 200

    def test_returns_items_array(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should return items array."""
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/processes"
        )
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_includes_completed_processes(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should include completed processes (unlike /active)."""
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/processes"
        )
        data = response.json()

        run_ids = [item["runId"] for item in data["items"]]
        # Should include the completed orchestrator
        assert "run-orch-1" in run_ids

    def test_returns_404_for_unknown_project(
        self, app_with_process_events: TestClient
    ) -> None:
        """Should return 404 for unknown project."""
        response = app_with_process_events.get(
            "/api/v1/projects/unknown-project-id/agents/processes"
        )
        assert response.status_code == 404


# =============================================================================
# GET /projects/{projectId}/agents/process-events Tests
# =============================================================================


class TestListProcessEvents:
    """Tests for GET /projects/{projectId}/agents/process-events endpoint."""

    def test_returns_200(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should return 200 OK."""
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/process-events"
        )
        assert response.status_code == 200

    def test_returns_items_array(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should return items array."""
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/process-events"
        )
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_returns_has_more_flag(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should return hasMore flag."""
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/process-events"
        )
        data = response.json()
        assert "hasMore" in data
        assert isinstance(data["hasMore"], bool)

    def test_event_has_required_fields(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should include required fields for each event."""
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/process-events"
        )
        data = response.json()

        required_fields = ["ts", "event", "runId"]

        for item in data["items"]:
            for field in required_fields:
                assert field in item, f"Missing field: {field}"

    def test_filter_by_run_id(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should filter by runId."""
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/process-events?runId=run-validation-1"
        )
        data = response.json()

        for item in data["items"]:
            assert item["runId"] == "run-validation-1"

    def test_filter_by_since(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should filter events since a given timestamp."""
        # Use a timestamp 3 minutes ago
        since = (datetime.now(timezone.utc) - timedelta(minutes=3)).isoformat()
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/process-events?since={since}"
        )
        data = response.json()

        # All returned events should be >= since
        for item in data["items"]:
            assert item["ts"] >= since

    def test_respects_limit(
        self, app_with_process_events: TestClient, project_id: str
    ) -> None:
        """Should respect limit parameter."""
        response = app_with_process_events.get(
            f"/api/v1/projects/{project_id}/agents/process-events?limit=2"
        )
        data = response.json()

        assert len(data["items"]) <= 2

    def test_returns_404_for_unknown_project(
        self, app_with_process_events: TestClient
    ) -> None:
        """Should return 404 for unknown project."""
        response = app_with_process_events.get(
            "/api/v1/projects/unknown-project-id/agents/process-events"
        )
        assert response.status_code == 404

    def test_returns_empty_for_no_events(
        self, app_with_empty_events: TestClient, empty_project_id: str
    ) -> None:
        """Should return empty list when no events exist."""
        response = app_with_empty_events.get(
            f"/api/v1/projects/{empty_project_id}/agents/process-events"
        )
        data = response.json()

        assert data["items"] == []
        assert data["hasMore"] is False


# =============================================================================
# AgentTrackingService Unit Tests
# =============================================================================


class TestAgentTrackingService:
    """Tests for the AgentTrackingService."""

    def test_parses_process_events_jsonl(
        self, mock_edison_project_with_process_events: Path
    ) -> None:
        """Should parse process-events.jsonl correctly."""
        from services.agent_tracking import AgentTrackingService

        service = AgentTrackingService(str(mock_edison_project_with_process_events))
        events = service.get_process_events()

        assert len(events) > 0
        assert all(hasattr(e, "ts") for e in events)
        assert all(hasattr(e, "event") for e in events)

    def test_computes_active_processes(
        self, mock_edison_project_with_process_events: Path
    ) -> None:
        """Should compute active processes (started but not completed)."""
        from services.agent_tracking import AgentTrackingService

        service = AgentTrackingService(str(mock_edison_project_with_process_events))
        active = service.get_active_agents()

        run_ids = [a.run_id for a in active]
        # Active agents
        assert "run-validation-1" in run_ids
        assert "run-impl-1" in run_ids
        # Completed agent should not be in active list
        assert "run-orch-1" not in run_ids

    def test_computes_staleness(
        self, mock_edison_project_with_process_events: Path
    ) -> None:
        """Should compute staleness based on last activity."""
        from services.agent_tracking import AgentTrackingService

        service = AgentTrackingService(str(mock_edison_project_with_process_events))
        active = service.get_active_agents()

        stale_agent = next(
            (a for a in active if a.run_id == "run-stale-1"), None
        )
        if stale_agent:
            assert stale_agent.is_stale is True

    def test_handles_missing_jsonl(
        self, mock_edison_project_empty_events: Path
    ) -> None:
        """Should handle missing JSONL file gracefully."""
        from services.agent_tracking import AgentTrackingService

        service = AgentTrackingService(str(mock_edison_project_empty_events))
        events = service.get_process_events()

        assert events == []

    def test_handles_malformed_jsonl(self, tmp_path: Path) -> None:
        """Should handle malformed JSONL gracefully."""
        from services.agent_tracking import AgentTrackingService

        project_path = tmp_path / "malformed-project"
        project_path.mkdir()
        (project_path / ".edison").mkdir()
        logs_dir = project_path / ".project" / "logs" / "edison"
        logs_dir.mkdir(parents=True)

        # Write malformed JSONL
        (logs_dir / "process-events.jsonl").write_text(
            "not valid json\n{also bad\n"
        )

        service = AgentTrackingService(str(project_path))
        events = service.get_process_events()

        # Should return empty or skip malformed lines
        assert isinstance(events, list)

    def test_filters_by_session(
        self, mock_edison_project_with_process_events: Path
    ) -> None:
        """Should filter active agents by session."""
        from services.agent_tracking import AgentTrackingService

        service = AgentTrackingService(str(mock_edison_project_with_process_events))
        active = service.get_active_agents(session_id="session-1")

        for agent in active:
            assert agent.session_id == "session-1"

    def test_filters_by_task(
        self, mock_edison_project_with_process_events: Path
    ) -> None:
        """Should filter active agents by task."""
        from services.agent_tracking import AgentTrackingService

        service = AgentTrackingService(str(mock_edison_project_with_process_events))
        active = service.get_active_agents(task_id="T001")

        for agent in active:
            assert agent.task_id == "T001"

    def test_filters_by_type(
        self, mock_edison_project_with_process_events: Path
    ) -> None:
        """Should filter active agents by type."""
        from services.agent_tracking import AgentTrackingService

        service = AgentTrackingService(str(mock_edison_project_with_process_events))
        active = service.get_active_agents(agent_type="validation")

        for agent in active:
            assert agent.type == "validation"


# =============================================================================
# Schema Tests
# =============================================================================


class TestAgentTrackingSchemas:
    """Tests for agent tracking Pydantic schemas."""

    def test_tracking_run_schema(self) -> None:
        """Should validate TrackingRun schema."""
        from api.schemas.agents import TrackingRun

        run = TrackingRun(
            run_id="run-1",
            type="validation",
            task_id="T001",
            session_id="session-1",
            validator_id="code-review",
            round=2,
            model="claude-3-5-sonnet",
            process_id=12345,
            hostname="localhost",
            started_at="2025-12-27T10:00:00Z",
            last_active_at="2025-12-27T10:05:00Z",
            is_running=True,
            is_stale=False,
            state="active",
        )

        assert run.run_id == "run-1"
        assert run.type == "validation"
        assert run.round == 2

    def test_tracking_run_camel_case_serialization(self) -> None:
        """Should serialize to camelCase for API response."""
        from api.schemas.agents import TrackingRun

        run = TrackingRun(
            run_id="run-1",
            type="implementation",
            task_id=None,
            session_id=None,
            validator_id=None,
            round=None,
            model=None,
            process_id=12345,
            hostname="localhost",
            started_at="2025-12-27T10:00:00Z",
            last_active_at="2025-12-27T10:05:00Z",
            is_running=True,
            is_stale=False,
            state="active",
        )

        data = run.model_dump(by_alias=True)
        assert "runId" in data
        assert "taskId" in data
        assert "sessionId" in data
        assert "validatorId" in data
        assert "processId" in data
        assert "startedAt" in data
        assert "lastActiveAt" in data
        assert "isRunning" in data
        assert "isStale" in data

    def test_process_event_schema(self) -> None:
        """Should validate ProcessEvent schema."""
        from api.schemas.agents import ProcessEvent

        event = ProcessEvent(
            ts="2025-12-27T10:00:00Z",
            event="started",
            run_id="run-1",
            pid=12345,
            hostname="localhost",
            kind="validation",
            task_id="T001",
            session_id="session-1",
        )

        assert event.event == "started"
        assert event.run_id == "run-1"

    def test_agent_active_response_schema(self) -> None:
        """Should validate AgentActiveResponse schema."""
        from api.schemas.agents import AgentActiveResponse

        response = AgentActiveResponse(items=[], total=0)

        assert response.total == 0
        assert response.items == []

    def test_process_events_response_schema(self) -> None:
        """Should validate ProcessEventsResponse schema."""
        from api.schemas.agents import ProcessEventsResponse

        response = ProcessEventsResponse(items=[], has_more=False)

        assert response.has_more is False
        assert response.items == []
