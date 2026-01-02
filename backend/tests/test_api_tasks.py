"""Tests for tasks listing endpoint (T020) and task readiness endpoint (T022).

RED Phase: These tests MUST fail initially as the endpoints don't exist yet.
Tests the unified tasks listing endpoint per US2 and api.md contracts.
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
    parent_id: str | None = None,
    child_ids: list[str] | None = None,
    depends_on: list[str] | None = None,
    blocks_tasks: list[str] | None = None,
    owner: str | None = None,
    tags: list[str] | None = None,
    priority: str | None = None,
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
    if parent_id:
        lines.append(f"parent_id: {parent_id}")
    if child_ids:
        lines.append(f"child_ids: {json.dumps(child_ids)}")
    if depends_on:
        lines.append(f"depends_on: {json.dumps(depends_on)}")
    if blocks_tasks:
        lines.append(f"blocks_tasks: {json.dumps(blocks_tasks)}")
    if owner:
        lines.append(f"owner: {owner}")
    if tags:
        lines.append(f"tags: {json.dumps(tags)}")
    if priority:
        lines.append(f"priority: {priority}")
    lines.append("created_at: '2025-12-27T10:00:00Z'")
    lines.append("updated_at: '2025-12-27T11:00:00Z'")
    lines.append("---")
    return "\n".join(lines)


@pytest.fixture
def mock_edison_project_with_tasks(tmp_path: Path) -> Path:
    """Create a mock Edison project with various tasks for testing."""
    project_path = tmp_path / "test-project"
    project_path.mkdir()

    # Create .edison directory (marks it as an Edison project)
    (project_path / ".edison").mkdir()

    # Create .project directory with tasks/sessions/qa
    project_dir = project_path / ".project"
    project_dir.mkdir()

    # Create task directories
    tasks_dir = project_dir / "tasks"
    tasks_dir.mkdir()
    for state in ["todo", "wip", "blocked", "done", "validated"]:
        (tasks_dir / state).mkdir()

    # Create global tasks (not session-scoped)
    # Task in todo state - no dependencies - should be ready
    (tasks_dir / "todo" / "T001.md").write_text(
        create_task_frontmatter(
            "T001",
            "Implement user authentication",
            depends_on=["T002"],
            tags=["auth", "security"],
            priority="P1",
        )
        + "\n# Task T001\nImplement user authentication flow."
    )

    # Task in wip state with parent/child hierarchy
    (tasks_dir / "wip" / "T002.md").write_text(
        create_task_frontmatter(
            "T002",
            "Setup database schema",
            child_ids=["T003"],
            blocks_tasks=["T001"],
        )
        + "\n# Task T002\nSetup database schema."
    )

    # Child task in todo
    (tasks_dir / "todo" / "T003.md").write_text(
        create_task_frontmatter(
            "T003",
            "Create user table",
            parent_id="T002",
        )
        + "\n# Task T003\nCreate user table migration."
    )

    # Task in done state - needs validation
    (tasks_dir / "done" / "T004.md").write_text(
        create_task_frontmatter(
            "T004",
            "Setup project structure",
        )
        + "\n# Task T004\nProject setup complete."
    )

    # Task in validated state
    (tasks_dir / "validated" / "T005.md").write_text(
        create_task_frontmatter(
            "T005",
            "Configure CI/CD",
            tags=["devops"],
        )
        + "\n# Task T005\nCI/CD configured."
    )

    # Task in blocked state - depends on incomplete tasks
    (tasks_dir / "blocked" / "T006.md").write_text(
        create_task_frontmatter(
            "T006",
            "Implement payment processing",
            depends_on=["T001", "T002"],
        )
        + "\n# Task T006\nBlocked on auth and db."
    )

    # Create sessions directory structure
    sessions_dir = project_dir / "sessions"
    sessions_dir.mkdir()
    (sessions_dir / "active").mkdir()
    (sessions_dir / "completed").mkdir()

    # Create an active session with session-scoped tasks
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

    # Create session-scoped task directories and tasks
    session_tasks_dir = session_dir / "tasks"
    session_tasks_dir.mkdir()
    for state in ["todo", "wip", "blocked", "done", "validated"]:
        (session_tasks_dir / state).mkdir()

    # Session-scoped task in wip
    (session_tasks_dir / "wip" / "T007.md").write_text(
        create_task_frontmatter(
            "T007",
            "Implement login form",
            session_id="session-001",
            tags=["ui", "auth"],
        )
        + "\n# Task T007\nSession-scoped login form task."
    )

    # Session-scoped task in todo - depends on T007
    (session_tasks_dir / "todo" / "T008.md").write_text(
        create_task_frontmatter(
            "T008",
            "Add form validation",
            session_id="session-001",
            depends_on=["T007"],
        )
        + "\n# Task T008\nForm validation for login."
    )

    # Create QA directories for validation status testing
    qa_dir = project_dir / "qa"
    qa_dir.mkdir()
    for state in ["waiting", "todo", "wip", "done", "validated"]:
        (qa_dir / state).mkdir()

    # QA record for T005 (validated task)
    (qa_dir / "validated" / "QA-T005.md").write_text(
        "---\nid: QA-T005\ntask_id: T005\nround: 1\n---\n# QA for T005"
    )

    # QA record for T002 (in_progress validation)
    (qa_dir / "wip" / "QA-T002.md").write_text(
        "---\nid: QA-T002\ntask_id: T002\nround: 1\n---\n# QA for T002"
    )

    # Create validation evidence directory
    evidence_dir = qa_dir / "validation-evidence" / "T005" / "round-1"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "bundle-summary.md").write_text("# Validation passed")

    # Create .git directory
    (project_path / ".git").mkdir()

    return project_path


@pytest.fixture
def app_with_tasks(
    mock_edison_project_with_tasks: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    """Create app with mocked scan roots pointing to project with tasks."""
    monkeypatch.setenv("SCAN_ROOTS", str(mock_edison_project_with_tasks.parent))
    monkeypatch.setenv("PIN_STORAGE_PATH", str(tmp_path / "pins.json"))

    from core.settings import get_settings

    get_settings.cache_clear()

    app = create_app()
    return TestClient(app)


@pytest.fixture
def project_id(app_with_tasks: TestClient) -> str:
    """Get the project ID from the discovered project."""
    response = app_with_tasks.get("/api/v1/projects")
    return str(response.json()["items"][0]["projectId"])


# =============================================================================
# T020: Tasks Listing Endpoint Tests
# =============================================================================


class TestListTasks:
    """Tests for GET /projects/{projectId}/tasks endpoint."""

    def test_list_tasks_returns_200(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should return 200 OK with list of tasks."""
        response = app_with_tasks.get(f"/api/v1/projects/{project_id}/tasks")
        assert response.status_code == 200

    def test_list_tasks_returns_items_array(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should return items array in response."""
        response = app_with_tasks.get(f"/api/v1/projects/{project_id}/tasks")
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_list_tasks_includes_global_and_session_tasks(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should include both global tasks and session-scoped tasks."""
        response = app_with_tasks.get(f"/api/v1/projects/{project_id}/tasks")
        data = response.json()

        task_ids = [t["taskId"] for t in data["items"]]
        # Global tasks
        assert "T001" in task_ids
        assert "T002" in task_ids
        # Session-scoped tasks
        assert "T007" in task_ids
        assert "T008" in task_ids

    def test_list_tasks_includes_pagination_info(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should include pagination info (total, limit, offset)."""
        response = app_with_tasks.get(f"/api/v1/projects/{project_id}/tasks")
        data = response.json()

        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert data["total"] == 8  # 6 global + 2 session-scoped

    def test_list_tasks_respects_limit(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should respect limit parameter."""
        response = app_with_tasks.get(f"/api/v1/projects/{project_id}/tasks?limit=3")
        data = response.json()

        assert data["limit"] == 3
        assert len(data["items"]) == 3

    def test_list_tasks_respects_offset(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should respect offset parameter."""
        response = app_with_tasks.get(f"/api/v1/projects/{project_id}/tasks?offset=5")
        data = response.json()

        assert data["offset"] == 5
        # With 8 total tasks and offset 5, should have 3 remaining
        assert len(data["items"]) == 3

    def test_list_tasks_task_has_required_fields(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should include all required fields per api.md contract."""
        response = app_with_tasks.get(f"/api/v1/projects/{project_id}/tasks")
        data = response.json()

        task = data["items"][0]
        required_fields = [
            "taskId",
            "title",
            "state",
            "sessionId",
            "validationStatus",
            "ready",
            "blockedBy",
            "createdAt",
            "updatedAt",
        ]
        for field in required_fields:
            assert field in task, f"Missing required field: {field}"

    def test_list_tasks_includes_hierarchy_fields_when_requested(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should include hierarchy fields when includeHierarchy=true."""
        response = app_with_tasks.get(
            f"/api/v1/projects/{project_id}/tasks?includeHierarchy=true"
        )
        data = response.json()

        # Find task with parent_id (T003)
        t003 = next((t for t in data["items"] if t["taskId"] == "T003"), None)
        assert t003 is not None
        assert "parentId" in t003
        assert t003["parentId"] == "T002"

        # Find task with child_ids (T002)
        t002 = next((t for t in data["items"] if t["taskId"] == "T002"), None)
        assert t002 is not None
        assert "childIds" in t002
        assert "T003" in t002["childIds"]

    def test_list_tasks_includes_dependency_fields(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should include dependsOn and blocksTasks fields."""
        response = app_with_tasks.get(
            f"/api/v1/projects/{project_id}/tasks?includeHierarchy=true"
        )
        data = response.json()

        # Find task with depends_on (T001)
        t001 = next((t for t in data["items"] if t["taskId"] == "T001"), None)
        assert t001 is not None
        assert "dependsOn" in t001
        assert "T002" in t001["dependsOn"]

        # Find task with blocks_tasks (T002)
        t002 = next((t for t in data["items"] if t["taskId"] == "T002"), None)
        assert t002 is not None
        assert "blocksTasks" in t002
        assert "T001" in t002["blocksTasks"]


class TestListTasksFiltering:
    """Tests for task list filtering."""

    def test_filter_by_session_id(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should filter tasks by sessionId."""
        response = app_with_tasks.get(
            f"/api/v1/projects/{project_id}/tasks?sessionId=session-001"
        )
        data = response.json()

        # Should only include session-001 tasks
        assert len(data["items"]) == 2
        for task in data["items"]:
            assert task["sessionId"] == "session-001"

    def test_filter_by_session_none(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should filter for unscoped tasks when sessionId=none."""
        response = app_with_tasks.get(
            f"/api/v1/projects/{project_id}/tasks?sessionId=none"
        )
        data = response.json()

        # Should only include global (unscoped) tasks
        assert len(data["items"]) == 6
        for task in data["items"]:
            assert task["sessionId"] is None

    def test_filter_by_state(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should filter tasks by state."""
        response = app_with_tasks.get(
            f"/api/v1/projects/{project_id}/tasks?state=todo"
        )
        data = response.json()

        # T001, T003 from global + T008 from session = 3 todo tasks
        assert len(data["items"]) == 3
        for task in data["items"]:
            assert task["state"] == "todo"

    def test_filter_by_multiple_states(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should filter tasks by multiple states (comma-separated)."""
        response = app_with_tasks.get(
            f"/api/v1/projects/{project_id}/tasks?state=todo,wip"
        )
        data = response.json()

        for task in data["items"]:
            assert task["state"] in ["todo", "wip"]

    def test_filter_by_validation_status(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should filter tasks by validationStatus."""
        response = app_with_tasks.get(
            f"/api/v1/projects/{project_id}/tasks?validationStatus=validated"
        )
        data = response.json()

        for task in data["items"]:
            assert task["validationStatus"] == "validated"

    def test_filter_by_parent_id(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should filter tasks by parentId."""
        response = app_with_tasks.get(
            f"/api/v1/projects/{project_id}/tasks?parentId=T002&includeHierarchy=true"
        )
        data = response.json()

        assert len(data["items"]) == 1
        assert data["items"][0]["taskId"] == "T003"
        assert data["items"][0]["parentId"] == "T002"

    def test_search_by_title(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should search tasks by title."""
        response = app_with_tasks.get(
            f"/api/v1/projects/{project_id}/tasks?search=authentication"
        )
        data = response.json()

        assert len(data["items"]) >= 1
        # T001 has "authentication" in title
        task_ids = [t["taskId"] for t in data["items"]]
        assert "T001" in task_ids


class TestListTasksValidationStatus:
    """Tests for task validation status computation."""

    def test_task_shows_validated_status(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Task in validated state should show validated status."""
        response = app_with_tasks.get(f"/api/v1/projects/{project_id}/tasks")
        data = response.json()

        t005 = next((t for t in data["items"] if t["taskId"] == "T005"), None)
        assert t005 is not None
        assert t005["validationStatus"] == "validated"

    def test_task_shows_in_progress_validation(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Task with in-progress QA should show in_progress status."""
        response = app_with_tasks.get(f"/api/v1/projects/{project_id}/tasks")
        data = response.json()

        t002 = next((t for t in data["items"] if t["taskId"] == "T002"), None)
        assert t002 is not None
        assert t002["validationStatus"] == "in_progress"

    def test_task_shows_needs_validation(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Task in done state without validated QA should show needs_validation."""
        response = app_with_tasks.get(f"/api/v1/projects/{project_id}/tasks")
        data = response.json()

        # T004 is in done state without any QA
        t004 = next((t for t in data["items"] if t["taskId"] == "T004"), None)
        assert t004 is not None
        assert t004["validationStatus"] == "needs_validation"


class TestListTasksReadiness:
    """Tests for task readiness computation in list."""

    def test_task_with_unmet_dependencies_is_not_ready(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Task depending on incomplete tasks should not be ready."""
        response = app_with_tasks.get(f"/api/v1/projects/{project_id}/tasks")
        data = response.json()

        # T001 depends on T002 which is in wip
        t001 = next((t for t in data["items"] if t["taskId"] == "T001"), None)
        assert t001 is not None
        assert t001["ready"] is False
        assert len(t001["blockedBy"]) > 0

    def test_task_with_no_dependencies_is_ready(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Task without dependencies (in todo/wip state) should be ready."""
        response = app_with_tasks.get(f"/api/v1/projects/{project_id}/tasks")
        data = response.json()

        # T003 has no depends_on - should be ready
        t003 = next((t for t in data["items"] if t["taskId"] == "T003"), None)
        assert t003 is not None
        assert t003["ready"] is True

    def test_blocked_by_includes_dependency_details(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """blockedBy should include structured blocking information."""
        response = app_with_tasks.get(f"/api/v1/projects/{project_id}/tasks")
        data = response.json()

        # T006 depends on T001 and T002
        t006 = next((t for t in data["items"] if t["taskId"] == "T006"), None)
        assert t006 is not None
        assert t006["ready"] is False

        blocked_by = t006["blockedBy"]
        assert len(blocked_by) >= 1

        # Check structure of blockedBy items
        for block in blocked_by:
            assert "dependencyId" in block
            assert "reason" in block


class TestListTasksErrors:
    """Tests for error handling in tasks endpoint."""

    def test_returns_404_for_unknown_project(
        self, app_with_tasks: TestClient
    ) -> None:
        """Should return 404 for non-existent project."""
        response = app_with_tasks.get("/api/v1/projects/nonexistent/tasks")
        assert response.status_code == 404

    def test_invalid_limit_returns_422(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should return 422 for invalid limit value."""
        response = app_with_tasks.get(
            f"/api/v1/projects/{project_id}/tasks?limit=-1"
        )
        assert response.status_code == 422

    def test_invalid_offset_returns_422(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should return 422 for invalid offset value."""
        response = app_with_tasks.get(
            f"/api/v1/projects/{project_id}/tasks?offset=-1"
        )
        assert response.status_code == 422


# =============================================================================
# T022: Task Readiness Endpoint Tests
# =============================================================================


class TestGetTaskReadiness:
    """Tests for GET /projects/{projectId}/tasks/{taskId}/readiness endpoint."""

    def test_readiness_returns_200_for_existing_task(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should return 200 for existing task."""
        response = app_with_tasks.get(
            f"/api/v1/projects/{project_id}/tasks/T003/readiness"
        )
        assert response.status_code == 200

    def test_readiness_returns_404_for_unknown_task(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should return 404 for unknown task."""
        response = app_with_tasks.get(
            f"/api/v1/projects/{project_id}/tasks/UNKNOWN-TASK/readiness"
        )
        assert response.status_code == 404

    def test_readiness_returns_404_for_unknown_project(
        self, app_with_tasks: TestClient
    ) -> None:
        """Should return 404 for unknown project."""
        response = app_with_tasks.get(
            "/api/v1/projects/unknown-project-id/tasks/T001/readiness"
        )
        assert response.status_code == 404

    def test_readiness_includes_required_fields(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Should include taskId, ready, blockedBy, and guardBlocks fields."""
        response = app_with_tasks.get(
            f"/api/v1/projects/{project_id}/tasks/T003/readiness"
        )
        data = response.json()

        assert "taskId" in data
        assert "ready" in data
        assert "blockedBy" in data
        assert "guardBlocks" in data

    def test_readiness_task_without_dependencies_is_ready(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Task without dependencies should be ready."""
        response = app_with_tasks.get(
            f"/api/v1/projects/{project_id}/tasks/T003/readiness"
        )
        data = response.json()

        assert data["taskId"] == "T003"
        assert data["ready"] is True
        assert data["blockedBy"] == []

    def test_readiness_task_with_unsatisfied_dependency_is_blocked(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """Task with unsatisfied dependency should be blocked."""
        response = app_with_tasks.get(
            f"/api/v1/projects/{project_id}/tasks/T001/readiness"
        )
        data = response.json()

        assert data["taskId"] == "T001"
        assert data["ready"] is False
        assert len(data["blockedBy"]) == 1
        assert data["blockedBy"][0]["dependencyId"] == "T002"
        assert data["blockedBy"][0]["dependencyState"] == "wip"
        assert "done" in data["blockedBy"][0]["requiredStates"]
        assert "validated" in data["blockedBy"][0]["requiredStates"]

    def test_readiness_blocked_by_has_correct_structure(
        self, app_with_tasks: TestClient, project_id: str
    ) -> None:
        """blockedBy items should have correct structure per API contract."""
        response = app_with_tasks.get(
            f"/api/v1/projects/{project_id}/tasks/T001/readiness"
        )
        data = response.json()

        blocked_by = data["blockedBy"][0]
        assert "dependencyId" in blocked_by
        assert "dependencyState" in blocked_by
        assert "requiredStates" in blocked_by
        assert "reason" in blocked_by
        assert isinstance(blocked_by["requiredStates"], list)
        assert isinstance(blocked_by["reason"], str)
        assert len(blocked_by["reason"]) > 0


# =============================================================================
# Schema Tests
# =============================================================================


class TestTaskSchemas:
    """Tests for task-related Pydantic schemas."""

    def test_task_list_item_schema(self) -> None:
        """Should validate TaskListItem schema."""
        from api.schemas.tasks import TaskListItem

        item = TaskListItem(
            task_id="T001",
            title="Test Task",
            state="todo",
            session_id=None,
            validation_status="needs_validation",
            ready=True,
            blocked_by=[],
            created_at="2025-12-27T10:00:00Z",
            updated_at="2025-12-27T10:00:00Z",
        )

        assert item.task_id == "T001"

    def test_task_list_item_with_hierarchy(self) -> None:
        """Should validate TaskListItem with hierarchy fields."""
        from api.schemas.tasks import TaskListItem

        item = TaskListItem(
            task_id="T001",
            title="Test Task",
            state="todo",
            session_id=None,
            parent_id="T000",
            child_ids=["T002"],
            depends_on=["T003"],
            blocks_tasks=["T004"],
            validation_status="needs_validation",
            ready=True,
            blocked_by=[],
            created_at="2025-12-27T10:00:00Z",
            updated_at="2025-12-27T10:00:00Z",
        )

        assert item.parent_id == "T000"
        assert "T002" in item.child_ids

    def test_blocked_by_item_schema(self) -> None:
        """Should validate BlockedByItem schema."""
        from api.schemas.tasks import BlockedByItem

        block = BlockedByItem(
            dependency_id="T001",
            dependency_state="wip",
            required_states=["done", "validated"],
            reason="Dependency T001 is not complete",
        )

        assert block.dependency_id == "T001"

    def test_guard_block_schema(self) -> None:
        """Should validate GuardBlock schema."""
        from api.schemas.tasks import GuardBlock

        block = GuardBlock(
            guard="session-active",
            reason="Session must be active to work on tasks",
        )

        assert block.guard == "session-active"

    def test_task_list_response_schema(self) -> None:
        """Should validate TaskListResponse schema."""
        from api.schemas.tasks import TaskListResponse

        response = TaskListResponse(
            items=[],
            total=0,
            limit=100,
            offset=0,
        )

        assert response.total == 0

    def test_task_readiness_response_schema(self) -> None:
        """Should validate TaskReadinessResponse schema."""
        from api.schemas.tasks import TaskReadinessResponse

        response = TaskReadinessResponse(
            task_id="T001",
            ready=True,
            blocked_by=[],
            guard_blocks=[],
        )

        assert response.task_id == "T001"
        assert response.ready is True

    def test_schema_json_serialization(self) -> None:
        """Should serialize to JSON with correct camelCase field names."""
        from api.schemas.tasks import TaskReadinessResponse, BlockedByItem

        blocked = BlockedByItem(
            dependency_id="T001",
            dependency_state="wip",
            required_states=["done", "validated"],
            reason="Test reason",
        )

        response = TaskReadinessResponse(
            task_id="T002",
            ready=False,
            blocked_by=[blocked],
            guard_blocks=[],
        )

        json_data = response.model_dump(mode="json", by_alias=True)

        assert "taskId" in json_data
        assert "blockedBy" in json_data
        assert "guardBlocks" in json_data
        assert json_data["blockedBy"][0]["dependencyId"] == "T001"
        assert json_data["blockedBy"][0]["dependencyState"] == "wip"
        assert json_data["blockedBy"][0]["requiredStates"] == ["done", "validated"]


# =============================================================================
# Service Tests
# =============================================================================


class TestTaskReaderService:
    """Tests for the task reader service."""

    def test_list_all_tasks(
        self, mock_edison_project_with_tasks: Path
    ) -> None:
        """Should list all tasks including session-scoped tasks."""
        from services.task_reader import TaskReaderService

        service = TaskReaderService(str(mock_edison_project_with_tasks))
        tasks = service.list_tasks()

        assert len(tasks) == 8
        task_ids = [t.task_id for t in tasks]
        assert "T001" in task_ids
        assert "T007" in task_ids  # Session-scoped

    def test_get_task_by_id(
        self, mock_edison_project_with_tasks: Path
    ) -> None:
        """Should get a specific task by ID."""
        from services.task_reader import TaskReaderService

        service = TaskReaderService(str(mock_edison_project_with_tasks))
        task = service.get_task("T001")

        assert task is not None
        assert task.task_id == "T001"
        assert task.title == "Implement user authentication"

    def test_get_task_returns_none_for_unknown(
        self, mock_edison_project_with_tasks: Path
    ) -> None:
        """Should return None for unknown task."""
        from services.task_reader import TaskReaderService

        service = TaskReaderService(str(mock_edison_project_with_tasks))
        task = service.get_task("UNKNOWN-TASK")

        assert task is None

    def test_filter_by_session(
        self, mock_edison_project_with_tasks: Path
    ) -> None:
        """Should filter tasks by session ID."""
        from services.task_reader import TaskReaderService

        service = TaskReaderService(str(mock_edison_project_with_tasks))
        tasks = service.list_tasks(session_id="session-001")

        assert len(tasks) == 2
        for t in tasks:
            assert t.session_id == "session-001"

    def test_filter_by_state(
        self, mock_edison_project_with_tasks: Path
    ) -> None:
        """Should filter tasks by state."""
        from services.task_reader import TaskReaderService

        service = TaskReaderService(str(mock_edison_project_with_tasks))
        tasks = service.list_tasks(states=["todo"])

        # T001, T003 (global) + T008 (session)
        assert len(tasks) == 3
        for t in tasks:
            assert t.state == "todo"

    def test_compute_readiness(
        self, mock_edison_project_with_tasks: Path
    ) -> None:
        """Should compute task readiness correctly."""
        from services.task_reader import TaskReaderService

        service = TaskReaderService(str(mock_edison_project_with_tasks))

        # T003 has no dependencies - should be ready
        readiness = service.compute_readiness("T003")
        assert readiness.ready is True
        assert readiness.blocked_by == []

        # T001 depends on T002 (wip) - should be blocked
        readiness = service.compute_readiness("T001")
        assert readiness.ready is False
        assert len(readiness.blocked_by) == 1
        assert readiness.blocked_by[0].dependency_id == "T002"

    def test_compute_validation_status(
        self, mock_edison_project_with_tasks: Path
    ) -> None:
        """Should compute validation status correctly."""
        from services.task_reader import TaskReaderService

        service = TaskReaderService(str(mock_edison_project_with_tasks))

        # T005 is in validated state
        status = service.get_validation_status("T005")
        assert status == "validated"

        # T002 has in-progress QA
        status = service.get_validation_status("T002")
        assert status == "in_progress"

        # T004 is in done state without QA
        status = service.get_validation_status("T004")
        assert status == "needs_validation"
