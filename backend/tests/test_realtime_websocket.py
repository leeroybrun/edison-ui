"""Tests for WebSocket realtime endpoint (T050).

RED Phase: These tests MUST fail initially as the endpoint doesn't exist yet.
Tests the push-first realtime updates per FR-006 and data-model.md contracts.

Protocol:
- Client sends: {"type": "subscribe", "subscriptionId": "...", "resource": "...", "params": {...}}
- Client sends: {"type": "unsubscribe", "subscriptionId": "..."}
- Server sends: {"type": "snapshot", "subscriptionId": "...", "revision": N, "data": [...]}
- Server sends: {"type": "upsert", "subscriptionId": "...", "revision": N, "data": {...}}
- Server sends: {"type": "delete", "subscriptionId": "...", "revision": N, "id": "..."}
- Server sends: {"type": "error", "subscriptionId": "...", "code": "...", "message": "..."}
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import create_app


def create_task_frontmatter(
    task_id: str,
    title: str,
    task_type: str = "implementation",
    session_id: str | None = None,
) -> str:
    """Create YAML frontmatter for a task file."""
    lines = [
        "---",
        f"id: {task_id}",
        f"title: {title}",
        f"type: {task_type}",
    ]
    if session_id:
        lines.append(f"session_id: {session_id}")
    lines.append("created_at: '2025-12-27T10:00:00Z'")
    lines.append("updated_at: '2025-12-27T11:00:00Z'")
    lines.append("---")
    return "\n".join(lines)


@pytest.fixture
def mock_edison_project_for_realtime(tmp_path: Path) -> Path:
    """Create a mock Edison project for realtime testing."""
    project_path = tmp_path / "test-project"
    project_path.mkdir()

    # Create .edison directory (marks it as an Edison project)
    (project_path / ".edison").mkdir()

    # Create .project directory with tasks
    project_dir = project_path / ".project"
    project_dir.mkdir()

    # Create task directories
    tasks_dir = project_dir / "tasks"
    tasks_dir.mkdir()
    for state in ["todo", "wip", "blocked", "done", "validated"]:
        (tasks_dir / state).mkdir()

    # Create sample tasks
    (tasks_dir / "todo" / "T001.md").write_text(
        create_task_frontmatter("T001", "First task")
        + "\n# Task T001\nFirst task description."
    )
    (tasks_dir / "wip" / "T002.md").write_text(
        create_task_frontmatter("T002", "Second task")
        + "\n# Task T002\nSecond task in progress."
    )
    (tasks_dir / "done" / "T003.md").write_text(
        create_task_frontmatter("T003", "Third task")
        + "\n# Task T003\nThird task completed."
    )

    # Create sessions directory structure
    sessions_dir = project_dir / "sessions"
    sessions_dir.mkdir()
    (sessions_dir / "active").mkdir()
    (sessions_dir / "completed").mkdir()

    # Create an active session
    session_dir = sessions_dir / "active" / "session-001"
    session_dir.mkdir()
    session_json = {
        "id": "session-001",
        "state": "active",
        "phase": "implementation",
        "meta": {
            "sessionId": "session-001",
            "createdAt": "2025-12-27T10:00:00Z",
            "lastActive": "2025-12-27T10:00:00Z",
        },
    }
    (session_dir / "session.json").write_text(json.dumps(session_json))

    # Create QA directories
    qa_dir = project_dir / "qa"
    qa_dir.mkdir()
    for state in ["waiting", "todo", "wip", "done", "validated"]:
        (qa_dir / state).mkdir()

    # Create .git directory
    (project_path / ".git").mkdir()

    return project_path


@pytest.fixture
def app_for_realtime(
    mock_edison_project_for_realtime: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    """Create app with mocked scan roots for realtime testing."""
    monkeypatch.setenv("SCAN_ROOTS", str(mock_edison_project_for_realtime.parent))
    monkeypatch.setenv("PIN_STORAGE_PATH", str(tmp_path / "pins.json"))

    from core.settings import get_settings

    get_settings.cache_clear()

    app = create_app()
    return TestClient(app)


@pytest.fixture
def project_id(app_for_realtime: TestClient) -> str:
    """Get the project ID from the discovered project."""
    response = app_for_realtime.get("/api/v1/projects")
    return str(response.json()["items"][0]["projectId"])


# =============================================================================
# WebSocket Connection Tests
# =============================================================================


class TestWebSocketConnection:
    """Tests for WebSocket connection lifecycle."""

    def test_websocket_endpoint_exists(self, app_for_realtime: TestClient) -> None:
        """WebSocket endpoint should exist at /api/v1/ws/realtime."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            # Connection should be established
            assert websocket is not None

    def test_websocket_accepts_connection(self, app_for_realtime: TestClient) -> None:
        """WebSocket should accept connections and stay open."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            # Send a simple ping-like message to verify connection
            websocket.send_json({"type": "ping"})
            # Should not raise exception

    def test_websocket_closes_gracefully(self, app_for_realtime: TestClient) -> None:
        """WebSocket should close gracefully when client disconnects."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            websocket.close()
            # Should not raise exception


# =============================================================================
# Subscribe/Unsubscribe Protocol Tests
# =============================================================================


class TestSubscribeProtocol:
    """Tests for subscribe message handling."""

    def test_subscribe_to_tasks_returns_snapshot(
        self, app_for_realtime: TestClient, project_id: str
    ) -> None:
        """Subscribe to tasks should return a snapshot message."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "sub-001",
                    "resource": "tasks",
                    "params": {"projectId": project_id},
                }
            )

            response = websocket.receive_json()
            assert response["type"] == "snapshot"
            assert response["subscriptionId"] == "sub-001"
            assert "revision" in response
            assert "data" in response
            assert isinstance(response["data"], list)

    def test_subscribe_snapshot_includes_tasks(
        self, app_for_realtime: TestClient, project_id: str
    ) -> None:
        """Snapshot should include task data."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "sub-tasks",
                    "resource": "tasks",
                    "params": {"projectId": project_id},
                }
            )

            response = websocket.receive_json()
            assert response["type"] == "snapshot"
            task_ids = [t["taskId"] for t in response["data"]]
            assert "T001" in task_ids
            assert "T002" in task_ids
            assert "T003" in task_ids

    def test_subscribe_to_sessions_returns_snapshot(
        self, app_for_realtime: TestClient, project_id: str
    ) -> None:
        """Subscribe to sessions should return a snapshot message."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "sub-sessions",
                    "resource": "sessions",
                    "params": {"projectId": project_id},
                }
            )

            response = websocket.receive_json()
            assert response["type"] == "snapshot"
            assert response["subscriptionId"] == "sub-sessions"
            assert "data" in response

    def test_subscribe_to_qa_returns_snapshot(
        self, app_for_realtime: TestClient, project_id: str
    ) -> None:
        """Subscribe to qa should return a snapshot message."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "sub-qa",
                    "resource": "qa",
                    "params": {"projectId": project_id},
                }
            )

            response = websocket.receive_json()
            assert response["type"] == "snapshot"
            assert response["subscriptionId"] == "sub-qa"

    def test_subscribe_to_projects_returns_snapshot(
        self, app_for_realtime: TestClient
    ) -> None:
        """Subscribe to projects should return a snapshot message."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "sub-projects",
                    "resource": "projects",
                    "params": {},
                }
            )

            response = websocket.receive_json()
            assert response["type"] == "snapshot"
            assert response["subscriptionId"] == "sub-projects"

    def test_multiple_subscriptions_on_same_connection(
        self, app_for_realtime: TestClient, project_id: str
    ) -> None:
        """Single connection should handle multiple subscriptions."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            # First subscription
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "sub-1",
                    "resource": "tasks",
                    "params": {"projectId": project_id},
                }
            )
            response1 = websocket.receive_json()
            assert response1["subscriptionId"] == "sub-1"

            # Second subscription
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "sub-2",
                    "resource": "sessions",
                    "params": {"projectId": project_id},
                }
            )
            response2 = websocket.receive_json()
            assert response2["subscriptionId"] == "sub-2"


class TestUnsubscribeProtocol:
    """Tests for unsubscribe message handling."""

    def test_unsubscribe_removes_subscription(
        self, app_for_realtime: TestClient, project_id: str
    ) -> None:
        """Unsubscribe should remove the subscription."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            # Subscribe first
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "sub-to-remove",
                    "resource": "tasks",
                    "params": {"projectId": project_id},
                }
            )
            websocket.receive_json()  # Consume snapshot

            # Unsubscribe
            websocket.send_json(
                {
                    "type": "unsubscribe",
                    "subscriptionId": "sub-to-remove",
                }
            )

            # Should not raise exception; connection should remain open

    def test_unsubscribe_unknown_subscription_returns_error(
        self, app_for_realtime: TestClient
    ) -> None:
        """Unsubscribe for unknown subscription should return error."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            websocket.send_json(
                {
                    "type": "unsubscribe",
                    "subscriptionId": "non-existent",
                }
            )

            response = websocket.receive_json()
            assert response["type"] == "error"
            assert response["subscriptionId"] == "non-existent"
            assert "code" in response
            assert "message" in response


# =============================================================================
# Revision Handling Tests
# =============================================================================


class TestRevisionHandling:
    """Tests for revision-based stale update protection."""

    def test_snapshot_includes_revision(
        self, app_for_realtime: TestClient, project_id: str
    ) -> None:
        """Snapshot messages should include a revision number."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "sub-rev",
                    "resource": "tasks",
                    "params": {"projectId": project_id},
                }
            )

            response = websocket.receive_json()
            assert "revision" in response
            assert isinstance(response["revision"], int)
            assert response["revision"] >= 0

    def test_revision_is_monotonically_increasing(
        self, app_for_realtime: TestClient, project_id: str
    ) -> None:
        """Revisions should be monotonically increasing per subscription."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "sub-mono",
                    "resource": "tasks",
                    "params": {"projectId": project_id},
                }
            )

            response = websocket.receive_json()
            first_revision = response["revision"]
            assert first_revision >= 0

            # If we get subsequent messages, they should have higher revisions
            # This will be tested more thoroughly when updates are implemented


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling in WebSocket protocol."""

    def test_invalid_json_returns_error(self, app_for_realtime: TestClient) -> None:
        """Invalid JSON should return an error message."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            websocket.send_text("not valid json")

            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "code" in response
            assert response["code"] == "INVALID_JSON"

    def test_missing_type_returns_error(self, app_for_realtime: TestClient) -> None:
        """Message without type field should return error."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            websocket.send_json({"subscriptionId": "sub-no-type"})

            response = websocket.receive_json()
            assert response["type"] == "error"
            assert response["code"] == "INVALID_MESSAGE"

    def test_unknown_message_type_returns_error(
        self, app_for_realtime: TestClient
    ) -> None:
        """Unknown message type should return error."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            websocket.send_json(
                {
                    "type": "unknown_type",
                    "subscriptionId": "sub-unknown",
                }
            )

            response = websocket.receive_json()
            assert response["type"] == "error"
            assert response["code"] == "UNKNOWN_MESSAGE_TYPE"

    def test_subscribe_missing_subscription_id_returns_error(
        self, app_for_realtime: TestClient
    ) -> None:
        """Subscribe without subscriptionId should return error."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            websocket.send_json(
                {
                    "type": "subscribe",
                    "resource": "tasks",
                    "params": {},
                }
            )

            response = websocket.receive_json()
            assert response["type"] == "error"
            assert response["code"] == "INVALID_MESSAGE"

    def test_subscribe_missing_resource_returns_error(
        self, app_for_realtime: TestClient
    ) -> None:
        """Subscribe without resource should return error."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "sub-no-resource",
                    "params": {},
                }
            )

            response = websocket.receive_json()
            assert response["type"] == "error"
            assert response["code"] == "INVALID_MESSAGE"

    def test_subscribe_invalid_resource_returns_error(
        self, app_for_realtime: TestClient
    ) -> None:
        """Subscribe with invalid resource should return error."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "sub-invalid-resource",
                    "resource": "invalid_resource",
                    "params": {},
                }
            )

            response = websocket.receive_json()
            assert response["type"] == "error"
            assert response["code"] == "INVALID_RESOURCE"

    def test_subscribe_missing_project_id_for_tasks_returns_error(
        self, app_for_realtime: TestClient
    ) -> None:
        """Subscribe to tasks without projectId should return error."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "sub-no-project",
                    "resource": "tasks",
                    "params": {},
                }
            )

            response = websocket.receive_json()
            assert response["type"] == "error"
            assert response["code"] == "MISSING_PARAM"

    def test_subscribe_nonexistent_project_returns_error(
        self, app_for_realtime: TestClient
    ) -> None:
        """Subscribe with non-existent projectId should return error."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "sub-bad-project",
                    "resource": "tasks",
                    "params": {"projectId": "non-existent-project-id"},
                }
            )

            response = websocket.receive_json()
            assert response["type"] == "error"
            assert response["code"] == "PROJECT_NOT_FOUND"

    def test_duplicate_subscription_id_returns_error(
        self, app_for_realtime: TestClient, project_id: str
    ) -> None:
        """Using duplicate subscription ID should return error."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            # First subscription
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "dup-sub",
                    "resource": "tasks",
                    "params": {"projectId": project_id},
                }
            )
            websocket.receive_json()  # Consume snapshot

            # Duplicate subscription
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "dup-sub",
                    "resource": "sessions",
                    "params": {"projectId": project_id},
                }
            )

            response = websocket.receive_json()
            assert response["type"] == "error"
            assert response["code"] == "DUPLICATE_SUBSCRIPTION"


# =============================================================================
# Schema Tests
# =============================================================================


class TestRealtimeSchemas:
    """Tests for realtime message Pydantic schemas."""

    def test_subscribe_message_schema(self) -> None:
        """Should validate SubscribeMessage schema."""
        from api.schemas.realtime import SubscribeMessage

        msg = SubscribeMessage(
            type="subscribe",
            subscription_id="sub-001",
            resource="tasks",
            params={"projectId": "project-123"},
        )

        assert msg.type == "subscribe"
        assert msg.subscription_id == "sub-001"
        assert msg.resource == "tasks"
        assert msg.params["projectId"] == "project-123"

    def test_unsubscribe_message_schema(self) -> None:
        """Should validate UnsubscribeMessage schema."""
        from api.schemas.realtime import UnsubscribeMessage

        msg = UnsubscribeMessage(
            type="unsubscribe",
            subscription_id="sub-001",
        )

        assert msg.type == "unsubscribe"
        assert msg.subscription_id == "sub-001"

    def test_snapshot_message_schema(self) -> None:
        """Should validate SnapshotMessage schema."""
        from api.schemas.realtime import SnapshotMessage

        msg = SnapshotMessage(
            type="snapshot",
            subscription_id="sub-001",
            revision=1,
            data=[{"taskId": "T001", "title": "Task 1"}],
        )

        assert msg.type == "snapshot"
        assert msg.subscription_id == "sub-001"
        assert msg.revision == 1
        assert len(msg.data) == 1

    def test_upsert_message_schema(self) -> None:
        """Should validate UpsertMessage schema."""
        from api.schemas.realtime import UpsertMessage

        msg = UpsertMessage(
            type="upsert",
            subscription_id="sub-001",
            revision=2,
            data={"taskId": "T001", "title": "Updated Task 1"},
        )

        assert msg.type == "upsert"
        assert msg.revision == 2

    def test_delete_message_schema(self) -> None:
        """Should validate DeleteMessage schema."""
        from api.schemas.realtime import DeleteMessage

        msg = DeleteMessage(
            type="delete",
            subscription_id="sub-001",
            revision=3,
            id="T001",
        )

        assert msg.type == "delete"
        assert msg.id == "T001"

    def test_error_message_schema(self) -> None:
        """Should validate ErrorMessage schema."""
        from api.schemas.realtime import ErrorMessage

        msg = ErrorMessage(
            type="error",
            subscription_id="sub-001",
            code="INVALID_MESSAGE",
            message="Missing required field: resource",
        )

        assert msg.type == "error"
        assert msg.code == "INVALID_MESSAGE"

    def test_error_message_without_subscription_id(self) -> None:
        """Error message should allow None subscription_id for connection-level errors."""
        from api.schemas.realtime import ErrorMessage

        msg = ErrorMessage(
            type="error",
            subscription_id=None,
            code="INVALID_JSON",
            message="Could not parse JSON",
        )

        assert msg.subscription_id is None

    def test_schema_json_serialization(self) -> None:
        """Should serialize to JSON with correct camelCase field names."""
        from api.schemas.realtime import SnapshotMessage

        msg = SnapshotMessage(
            type="snapshot",
            subscription_id="sub-001",
            revision=1,
            data=[],
        )

        json_data = msg.model_dump(mode="json", by_alias=True)

        assert "subscriptionId" in json_data
        assert json_data["subscriptionId"] == "sub-001"


# =============================================================================
# Connection Manager Tests
# =============================================================================


class TestConnectionManager:
    """Tests for WebSocket connection manager service."""

    def test_connection_manager_exists(self) -> None:
        """ConnectionManager class should exist."""
        from services.realtime.connection_manager import ConnectionManager

        manager = ConnectionManager()
        assert manager is not None

    def test_connection_manager_tracks_connections(self) -> None:
        """ConnectionManager should track active connections."""
        from services.realtime.connection_manager import ConnectionManager

        manager = ConnectionManager()
        assert manager.active_connection_count == 0


class TestSubscriptionManager:
    """Tests for subscription manager service."""

    def test_subscription_manager_exists(self) -> None:
        """SubscriptionManager class should exist."""
        from services.realtime.subscription_manager import SubscriptionManager

        manager = SubscriptionManager()
        assert manager is not None

    def test_subscription_manager_tracks_subscriptions(self) -> None:
        """SubscriptionManager should track active subscriptions."""
        from services.realtime.subscription_manager import SubscriptionManager

        manager = SubscriptionManager()
        assert manager.subscription_count == 0

    def test_subscription_manager_generates_revision(self) -> None:
        """SubscriptionManager should generate monotonic revisions."""
        from services.realtime.subscription_manager import SubscriptionManager

        manager = SubscriptionManager()
        rev1 = manager.get_next_revision("sub-001")
        rev2 = manager.get_next_revision("sub-001")

        assert rev2 > rev1


# =============================================================================
# Task Filtering in Subscriptions
# =============================================================================


class TestSubscriptionFiltering:
    """Tests for filtering in subscriptions."""

    def test_subscribe_tasks_with_state_filter(
        self, app_for_realtime: TestClient, project_id: str
    ) -> None:
        """Subscribe to tasks with state filter should return filtered snapshot."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "sub-filtered",
                    "resource": "tasks",
                    "params": {"projectId": project_id, "state": "todo"},
                }
            )

            response = websocket.receive_json()
            assert response["type"] == "snapshot"
            for task in response["data"]:
                assert task["state"] == "todo"

    def test_subscribe_tasks_with_session_filter(
        self, app_for_realtime: TestClient, project_id: str
    ) -> None:
        """Subscribe to tasks with session filter should return filtered snapshot."""
        with app_for_realtime.websocket_connect("/api/v1/ws/realtime") as websocket:
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "sub-session-filtered",
                    "resource": "tasks",
                    "params": {"projectId": project_id, "sessionId": "session-001"},
                }
            )

            response = websocket.receive_json()
            assert response["type"] == "snapshot"
            # All returned tasks should have the session ID or be empty
            for task in response["data"]:
                assert task.get("sessionId") == "session-001"
