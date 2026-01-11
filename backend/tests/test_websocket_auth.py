"""Tests for WebSocket authentication in exposed mode (T063).

RED Phase: These tests MUST fail initially as WebSocket auth doesn't exist yet.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.fixture
def localhost_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create app in localhost mode."""
    settings_file = tmp_path / "settings.json"
    pairing_file = tmp_path / "pairing.json"

    settings_data = {
        "scanRoots": [str(tmp_path / "projects")],
        "displayName": "Test User",
        "firstRunComplete": True,
        "exposureMode": "localhost",
    }
    settings_file.write_text(json.dumps(settings_data))

    monkeypatch.setenv("SETTINGS_FILE", str(settings_file))
    monkeypatch.setenv("PAIRING_FILE", str(pairing_file))
    monkeypatch.setenv("SCAN_ROOTS", str(tmp_path / "projects"))

    (tmp_path / "projects").mkdir()

    from core.settings import get_settings

    get_settings.cache_clear()

    app = create_app()
    return TestClient(app)


@pytest.fixture
def network_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create app in network-exposed mode."""
    settings_file = tmp_path / "settings.json"
    pairing_file = tmp_path / "pairing.json"

    settings_data = {
        "scanRoots": [str(tmp_path / "projects")],
        "displayName": "Test User",
        "firstRunComplete": True,
        "exposureMode": "network",
    }
    settings_file.write_text(json.dumps(settings_data))

    monkeypatch.setenv("SETTINGS_FILE", str(settings_file))
    monkeypatch.setenv("PAIRING_FILE", str(pairing_file))
    monkeypatch.setenv("SCAN_ROOTS", str(tmp_path / "projects"))

    (tmp_path / "projects").mkdir()

    from core.settings import get_settings

    get_settings.cache_clear()

    app = create_app()
    return TestClient(app)


class TestWebSocketAuthLocalhostMode:
    """Tests for WebSocket in localhost mode (no auth required)."""

    def test_websocket_connects_without_auth_in_localhost_mode(
        self, localhost_app: TestClient
    ) -> None:
        """Should allow WebSocket connection without auth in localhost mode."""
        with localhost_app.websocket_connect("/api/v1/ws/realtime") as websocket:
            # Send a ping to verify connection is active
            websocket.send_json({"type": "ping"})
            # Connection should be established (no immediate close)
            # Just verify we can subscribe
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "test-sub",
                    "resource": "projects",
                }
            )
            response = websocket.receive_json()
            assert response["type"] == "snapshot"


class TestWebSocketAuthNetworkMode:
    """Tests for WebSocket in network-exposed mode (auth required)."""

    def test_websocket_rejects_connection_without_token(
        self, network_app: TestClient
    ) -> None:
        """Should reject WebSocket connection without token in network mode."""
        # WebSocket without token should receive auth error and close
        with network_app.websocket_connect("/api/v1/ws/realtime") as websocket:
            # First message should be an auth error
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert response["code"] == "AUTH_REQUIRED"

    def test_websocket_rejects_connection_with_invalid_token(
        self, network_app: TestClient
    ) -> None:
        """Should reject WebSocket connection with invalid token."""
        with network_app.websocket_connect(
            "/api/v1/ws/realtime?token=invalid-token"
        ) as websocket:
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert response["code"] == "AUTH_REQUIRED"

    def test_websocket_connects_with_valid_token(self, network_app: TestClient) -> None:
        """Should allow WebSocket connection with valid token."""
        # First, get a valid token via pairing
        start_response = network_app.post("/api/v1/pairing/start")
        display_code = start_response.json()["displayCode"]

        complete_response = network_app.post(
            "/api/v1/pairing/complete", json={"displayCode": display_code}
        )
        token = complete_response.json()["token"]

        # Now connect WebSocket with token
        with network_app.websocket_connect(
            f"/api/v1/ws/realtime?token={token}"
        ) as websocket:
            # Should be able to subscribe
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "test-sub",
                    "resource": "projects",
                }
            )
            response = websocket.receive_json()
            assert response["type"] == "snapshot"

    def test_websocket_rejects_connection_with_revoked_token(
        self, network_app: TestClient
    ) -> None:
        """Should reject WebSocket connection with revoked token."""
        # Get a token
        start_response = network_app.post("/api/v1/pairing/start")
        display_code = start_response.json()["displayCode"]

        complete_response = network_app.post(
            "/api/v1/pairing/complete", json={"displayCode": display_code}
        )
        token = complete_response.json()["token"]

        # Revoke the token (need to use localhost for this since we don't have auth)
        # Actually, we already have a token, so we can use it to revoke itself
        network_app.delete(
            "/api/v1/pairing/token", headers={"Authorization": f"Bearer {token}"}
        )

        # Try to connect with revoked token
        with network_app.websocket_connect(
            f"/api/v1/ws/realtime?token={token}"
        ) as websocket:
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert response["code"] == "AUTH_REQUIRED"

    def test_websocket_error_message_for_unauthorized(
        self, network_app: TestClient
    ) -> None:
        """Should send auth error before closing connection."""
        with network_app.websocket_connect("/api/v1/ws/realtime") as websocket:
            # The first message should be an auth error
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert response["code"] == "AUTH_REQUIRED"
            assert (
                "Authorization" in response["message"]
                or "authorization" in response["message"].lower()
            )


class TestWebSocketAuthTokenInHeader:
    """Tests for WebSocket auth via Sec-WebSocket-Protocol header."""

    def test_websocket_accepts_token_in_protocol_header(
        self, network_app: TestClient
    ) -> None:
        """Should accept token passed via Sec-WebSocket-Protocol header."""
        # Get a token
        start_response = network_app.post("/api/v1/pairing/start")
        display_code = start_response.json()["displayCode"]

        complete_response = network_app.post(
            "/api/v1/pairing/complete", json={"displayCode": display_code}
        )
        token = complete_response.json()["token"]

        # Connect using token in subprotocol header
        # Format: "bearer.{token}"
        with network_app.websocket_connect(
            "/api/v1/ws/realtime", subprotocols=[f"bearer.{token}"]
        ) as websocket:
            websocket.send_json(
                {
                    "type": "subscribe",
                    "subscriptionId": "test-sub",
                    "resource": "projects",
                }
            )
            response = websocket.receive_json()
            assert response["type"] == "snapshot"
