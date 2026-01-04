"""Tests for QA validation trigger endpoints (T042).

RED Phase: These tests verify the preview -> confirm/apply pattern for:
- POST /projects/{projectId}/qa/trigger/preview
- POST /projects/{projectId}/qa/trigger
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


def create_qa_frontmatter(
    task_id: str,
    qa_id: str,
    state: str = "todo",
    verdict: str | None = None,
    round_num: int | None = None,
    validators: list[str] | None = None,
) -> str:
    """Create QA file frontmatter."""
    lines = [
        "---",
        f"id: {qa_id}",
        f"task_id: {task_id}",
    ]
    if round_num:
        lines.append(f"round: {round_num}")
    if verdict:
        lines.append(f"verdict: {verdict}")
    if validators:
        lines.append("validators:")
        for v in validators:
            lines.append(f"  - {v}")
    lines.append("created_at: '2025-01-01T10:00:00Z'")
    lines.append("updated_at: '2025-01-01T10:00:00Z'")
    lines.append("---")
    return "\n".join(lines)


@pytest.fixture
def project_with_trigger_setup(tmp_path: Path) -> Path:
    """Create a mock Edison project for testing trigger endpoints."""
    project_path = tmp_path / "trigger-test-project"
    project_path.mkdir()

    # Create .edison directory (marks it as an Edison project)
    (project_path / ".edison").mkdir()

    # Create .project directory structure
    project_dir = project_path / ".project"
    project_dir.mkdir()

    # Create task directories
    tasks_dir = project_dir / "tasks"
    tasks_dir.mkdir()
    for state in ["todo", "wip", "blocked", "done", "validated"]:
        (tasks_dir / state).mkdir()

    # Task in done state - ready for validation trigger
    (tasks_dir / "done" / "T001.md").write_text(
        create_task_frontmatter("T001", "Completed task")
        + "\n# Task T001\nReady for validation."
    )

    # Task in wip state - NOT ready
    (tasks_dir / "wip" / "T002.md").write_text(
        create_task_frontmatter("T002", "Task in progress")
        + "\n# Task T002\nStill working."
    )

    # Task in done state with active QA - has active validation
    (tasks_dir / "done" / "T003.md").write_text(
        create_task_frontmatter("T003", "Task with active QA")
        + "\n# Task T003\nHas active validation."
    )

    # Task in validated state
    (tasks_dir / "validated" / "T004.md").write_text(
        create_task_frontmatter("T004", "Validated task")
        + "\n# Task T004\nAlready validated."
    )

    # Create QA directories
    qa_dir = project_dir / "qa"
    qa_dir.mkdir()
    for state in ["waiting", "todo", "wip", "done", "validated"]:
        (qa_dir / state).mkdir()

    # QA for T003 in wip state (active validation)
    (qa_dir / "wip" / "T003-qa.md").write_text(
        create_qa_frontmatter(
            "T003", "QA-T003", state="wip", round_num=1,
            validators=["code-review"]
        )
        + "\n# QA T003\nValidation in progress."
    )

    # Create sessions directory structure
    sessions_dir = project_dir / "sessions"
    sessions_dir.mkdir()
    for state in ["draft", "active", "paused", "completed", "abandoned"]:
        (sessions_dir / state).mkdir()

    # Create logs directory for audit
    logs_dir = project_dir / "logs" / "edison"
    logs_dir.mkdir(parents=True)

    # Create .git directory
    (project_path / ".git").mkdir()

    return project_path


@pytest.fixture
def app_with_trigger(
    project_with_trigger_setup: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    """Create app with mocked scan roots."""
    monkeypatch.setenv("SCAN_ROOTS", str(project_with_trigger_setup.parent))
    monkeypatch.setenv("PIN_STORAGE_PATH", str(tmp_path / "pins.json"))

    from core.settings import get_settings

    get_settings.cache_clear()

    app = create_app()
    return TestClient(app)


@pytest.fixture
def project_id(app_with_trigger: TestClient) -> str:
    """Get the project ID from the discovered project."""
    response = app_with_trigger.get("/api/v1/projects")
    return str(response.json()["items"][0]["projectId"])


# =============================================================================
# Validation Trigger Preview Tests
# =============================================================================


class TestValidationTriggerPreview:
    """Tests for POST /projects/{projectId}/qa/trigger/preview endpoint."""

    def test_preview_returns_200_for_valid_task(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Should return 200 for valid trigger preview."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger/preview",
            json={"taskId": "T001"},
        )
        assert response.status_code == 200

    def test_preview_returns_valid_true_for_done_task(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Should return valid=true for task in done state."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger/preview",
            json={"taskId": "T001"},
        )
        data = response.json()
        assert data["valid"] is True
        assert data["taskId"] == "T001"
        assert data["taskState"] == "done"

    def test_preview_returns_suggested_validators(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Should return suggested validators for valid preview."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger/preview",
            json={"taskId": "T001"},
        )
        data = response.json()
        assert "suggestedValidators" in data
        assert isinstance(data["suggestedValidators"], list)

    def test_preview_returns_valid_false_for_wip_task(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Should return valid=false for task not in done state."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger/preview",
            json={"taskId": "T002"},
        )
        data = response.json()
        assert data["valid"] is False
        assert "guardFailures" in data
        assert any(f["guard"] == "task-done" for f in data["guardFailures"])

    def test_preview_returns_valid_false_for_active_validation(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Should return valid=false when active validation exists."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger/preview",
            json={"taskId": "T003"},
        )
        data = response.json()
        assert data["valid"] is False
        assert any(f["guard"] == "no-active-validation" for f in data["guardFailures"])

    def test_preview_returns_valid_false_for_nonexistent_task(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Should return valid=false for non-existent task."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger/preview",
            json={"taskId": "T999"},
        )
        data = response.json()
        assert data["valid"] is False
        assert any(f["guard"] == "task-exists" for f in data["guardFailures"])

    def test_preview_returns_valid_false_for_validated_task(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Should return valid=false for already validated task."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger/preview",
            json={"taskId": "T004"},
        )
        data = response.json()
        assert data["valid"] is False
        assert any(f["guard"] == "task-done" for f in data["guardFailures"])

    def test_preview_accepts_validators_param(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Should accept validators parameter."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger/preview",
            json={
                "taskId": "T001",
                "validators": ["code-review", "test-coverage"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_preview_returns_valid_false_for_invalid_validators(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Should return valid=false for invalid validators."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger/preview",
            json={
                "taskId": "T001",
                "validators": ["invalid-validator"],
            },
        )
        data = response.json()
        assert data["valid"] is False
        assert any(f["guard"] == "validators-valid" for f in data["guardFailures"])

    def test_preview_returns_guard_warnings(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Should return guard warnings when present."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger/preview",
            json={"taskId": "T001"},
        )
        data = response.json()
        assert "guardWarnings" in data
        assert isinstance(data["guardWarnings"], list)

    def test_preview_returns_404_for_unknown_project(
        self, app_with_trigger: TestClient
    ) -> None:
        """Should return 404 for non-existent project."""
        response = app_with_trigger.post(
            "/api/v1/projects/unknown-project/qa/trigger/preview",
            json={"taskId": "T001"},
        )
        assert response.status_code == 404


# =============================================================================
# Validation Trigger Apply Tests
# =============================================================================


class TestValidationTriggerApply:
    """Tests for POST /projects/{projectId}/qa/trigger endpoint."""

    def test_trigger_returns_400_without_confirmed_flag(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Should return 400 if confirmed flag is not set."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger",
            json={"taskId": "T001"},
        )
        assert response.status_code == 400

    def test_trigger_returns_400_when_guards_fail(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Should return 400 when guards fail even with confirmed=true."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger",
            json={
                "taskId": "T002",  # wip task - not done
                "confirmed": True,
            },
        )
        assert response.status_code == 400

    def test_trigger_returns_200_for_valid_confirmed_request(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Should return 200 for valid confirmed trigger."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger",
            json={
                "taskId": "T001",
                "confirmed": True,
            },
        )
        assert response.status_code == 200

    def test_trigger_returns_qa_id(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Should return qaId in response."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger",
            json={
                "taskId": "T001",
                "confirmed": True,
            },
        )
        data = response.json()
        assert "qaId" in data
        assert data["qaId"] is not None

    def test_trigger_returns_task_id(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Should return taskId in response."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger",
            json={
                "taskId": "T001",
                "confirmed": True,
            },
        )
        data = response.json()
        assert "taskId" in data
        assert data["taskId"] == "T001"

    def test_trigger_returns_round_number(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Should return round number in response."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger",
            json={
                "taskId": "T001",
                "confirmed": True,
            },
        )
        data = response.json()
        assert "round" in data
        assert data["round"] == 1

    def test_trigger_returns_audit_entry_id(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Should return auditEntryId in response."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger",
            json={
                "taskId": "T001",
                "confirmed": True,
            },
        )
        data = response.json()
        assert "auditEntryId" in data
        assert data["auditEntryId"] is not None

    def test_trigger_with_validators_creates_qa_with_validators(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Should create QA with specified validators."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger",
            json={
                "taskId": "T001",
                "validators": ["code-review"],
                "confirmed": True,
            },
        )
        assert response.status_code == 200

    def test_trigger_returns_404_for_unknown_project(
        self, app_with_trigger: TestClient
    ) -> None:
        """Should return 404 for non-existent project."""
        response = app_with_trigger.post(
            "/api/v1/projects/unknown-project/qa/trigger",
            json={"taskId": "T001", "confirmed": True},
        )
        assert response.status_code == 404


# =============================================================================
# Audit Integration Tests
# =============================================================================


class TestTriggerAuditIntegration:
    """Tests for audit logging on validation trigger."""

    def test_trigger_writes_audit_entry(
        self,
        app_with_trigger: TestClient,
        project_id: str,
        project_with_trigger_setup: Path,
    ) -> None:
        """Should write audit entry on validation trigger."""
        import glob as globmod
        from datetime import date

        # Trigger validation
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger",
            json={
                "taskId": "T001",
                "confirmed": True,
            },
        )
        assert response.status_code == 200

        # Check audit log exists
        today = date.today().isoformat()
        log_pattern = str(
            project_with_trigger_setup / ".project" / "logs" / "edison" / f"audit-{today}.jsonl"
        )
        log_files = globmod.glob(log_pattern)
        assert len(log_files) == 1

        # Read and verify audit entry
        with open(log_files[0]) as f:
            lines = f.readlines()
        assert len(lines) >= 1

        last_entry = json.loads(lines[-1])
        assert last_entry["action_type"] == "qa.trigger"
        assert last_entry["outcome"] == "success"


# =============================================================================
# Schema Validation Tests
# =============================================================================


class TestTriggerSchemas:
    """Tests for request/response schema validation."""

    def test_preview_requires_task_id(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Should require taskId in preview request."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger/preview",
            json={},
        )
        assert response.status_code == 422

    def test_trigger_requires_task_id(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Should require taskId in trigger request."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger",
            json={"confirmed": True},
        )
        assert response.status_code == 422

    def test_guard_failure_has_required_fields(
        self, app_with_trigger: TestClient, project_id: str
    ) -> None:
        """Guard failure should have guard and reason fields."""
        response = app_with_trigger.post(
            f"/api/v1/projects/{project_id}/qa/trigger/preview",
            json={"taskId": "T999"},
        )
        data = response.json()
        assert data["valid"] is False
        failure = data["guardFailures"][0]
        assert "guard" in failure
        assert "reason" in failure
