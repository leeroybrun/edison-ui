"""Tests for activity routes (T044).

Tests for GET /projects/{projectId}/activity and /audit endpoints.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def project_id(client: TestClient) -> str:
    """Get a valid project ID from the API."""
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    if data["items"]:
        return data["items"][0]["project_id"]
    pytest.skip("No projects available for testing")


class TestActivityEndpoint:
    """Tests for GET /projects/{projectId}/activity endpoint."""

    def test_get_activity_returns_200(self, client: TestClient, project_id: str) -> None:
        """Activity endpoint returns 200 for valid project."""
        response = client.get(f"/api/v1/projects/{project_id}/activity")
        assert response.status_code == 200

    def test_get_activity_returns_expected_schema(
        self, client: TestClient, project_id: str
    ) -> None:
        """Activity endpoint returns expected response schema."""
        response = client.get(f"/api/v1/projects/{project_id}/activity")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "hasMore" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["hasMore"], bool)

    def test_get_activity_with_filters(
        self, client: TestClient, project_id: str
    ) -> None:
        """Activity endpoint accepts filter parameters."""
        response = client.get(
            f"/api/v1/projects/{project_id}/activity",
            params={
                "sessionId": "test-session",
                "taskId": "T001",
                "eventType": "task_created",
                "since": "2024-01-01T00:00:00Z",
                "limit": 25,
            },
        )
        assert response.status_code == 200

    def test_get_activity_not_found_for_invalid_project(
        self, client: TestClient
    ) -> None:
        """Activity endpoint returns 404 for invalid project."""
        response = client.get("/api/v1/projects/invalid-project-id/activity")
        assert response.status_code == 404


class TestAuditEndpoint:
    """Tests for GET /projects/{projectId}/audit endpoint."""

    def test_get_audit_returns_200(self, client: TestClient, project_id: str) -> None:
        """Audit endpoint returns 200 for valid project."""
        response = client.get(f"/api/v1/projects/{project_id}/audit")
        assert response.status_code == 200

    def test_get_audit_returns_expected_schema(
        self, client: TestClient, project_id: str
    ) -> None:
        """Audit endpoint returns expected response schema."""
        response = client.get(f"/api/v1/projects/{project_id}/audit")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "hasMore" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["hasMore"], bool)

    def test_get_audit_with_filters(self, client: TestClient, project_id: str) -> None:
        """Audit endpoint accepts filter parameters."""
        response = client.get(
            f"/api/v1/projects/{project_id}/audit",
            params={
                "sessionId": "test-session",
                "invocationId": "inv-123",
                "since": "2024-01-01T00:00:00Z",
                "limit": 25,
            },
        )
        assert response.status_code == 200

    def test_get_audit_not_found_for_invalid_project(self, client: TestClient) -> None:
        """Audit endpoint returns 404 for invalid project."""
        response = client.get("/api/v1/projects/invalid-project-id/audit")
        assert response.status_code == 404
