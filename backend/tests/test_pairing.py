"""Tests for pairing service and endpoints (T060, T061).

RED Phase: These tests MUST fail initially as the functionality doesn't exist yet.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.fixture
def clean_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create app with clean settings in tmp location."""
    settings_file = tmp_path / "settings.json"
    pairing_file = tmp_path / "pairing.json"

    # Create settings with localhost mode
    settings_data = {
        "scanRoots": [str(tmp_path / "projects")],
        "displayName": "Test User",
        "firstRunComplete": True,
        "exposureMode": "localhost",
    }
    settings_file.write_text(json.dumps(settings_data))

    monkeypatch.setenv("SETTINGS_FILE", str(settings_file))
    monkeypatch.setenv("PAIRING_FILE", str(pairing_file))

    (tmp_path / "projects").mkdir()

    from core.settings import get_settings

    get_settings.cache_clear()

    app = create_app()
    return TestClient(app)


@pytest.fixture
def network_exposed_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create app with network exposure mode."""
    settings_file = tmp_path / "settings.json"
    pairing_file = tmp_path / "pairing.json"

    # Create settings with network mode
    settings_data = {
        "scanRoots": [str(tmp_path / "projects")],
        "displayName": "Test User",
        "firstRunComplete": True,
        "exposureMode": "network",
    }
    settings_file.write_text(json.dumps(settings_data))

    monkeypatch.setenv("SETTINGS_FILE", str(settings_file))
    monkeypatch.setenv("PAIRING_FILE", str(pairing_file))

    (tmp_path / "projects").mkdir()

    from core.settings import get_settings

    get_settings.cache_clear()

    app = create_app()
    return TestClient(app)


# =============================================================================
# T060: Server Exposure Modes Tests
# =============================================================================


class TestExposureModeSettings:
    """Tests for exposure mode configuration."""

    def test_get_settings_returns_localhost_by_default(
        self, clean_app: TestClient
    ) -> None:
        """Should return exposureMode='localhost' by default."""
        response = clean_app.get("/api/v1/settings")
        data = response.json()

        assert response.status_code == 200
        assert data["exposureMode"] == "localhost"

    def test_get_settings_returns_network_when_configured_with_auth(
        self, network_exposed_app: TestClient
    ) -> None:
        """Should return exposureMode='network' when configured and authenticated."""
        # In network mode, we need to pair first to get a token
        start_response = network_exposed_app.post("/api/v1/pairing/start")
        display_code = start_response.json()["displayCode"]

        complete_response = network_exposed_app.post(
            "/api/v1/pairing/complete", json={"displayCode": display_code}
        )
        token = complete_response.json()["token"]

        # Now we can access settings with the token
        response = network_exposed_app.get(
            "/api/v1/settings", headers={"Authorization": f"Bearer {token}"}
        )
        data = response.json()

        assert response.status_code == 200
        assert data["exposureMode"] == "network"

    def test_cannot_update_exposure_mode_via_patch(self, clean_app: TestClient) -> None:
        """Should not allow exposureMode update via PATCH (not in allowlist)."""
        # Note: SettingsUpdateRequest schema doesn't include exposureMode
        # The field will be ignored by Pydantic
        response = clean_app.patch("/api/v1/settings", json={"exposureMode": "network"})

        # Request succeeds but exposureMode is not updated (not in schema)
        assert response.status_code == 200

        # Verify exposure mode hasn't changed
        settings_response = clean_app.get("/api/v1/settings")
        assert settings_response.json()["exposureMode"] == "localhost"


class TestExposureModeUpdate:
    """Tests for dedicated exposure mode update endpoint."""

    def test_update_exposure_mode_to_network(self, clean_app: TestClient) -> None:
        """Should be able to update exposureMode to 'network' via dedicated endpoint."""
        response = clean_app.post(
            "/api/v1/settings/exposure-mode", json={"exposureMode": "network"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["exposureMode"] == "network"

        # Note: After switching to network mode, we need auth to verify
        # So we pair first and then check
        start_response = clean_app.post("/api/v1/pairing/start")
        display_code = start_response.json()["displayCode"]
        complete_response = clean_app.post(
            "/api/v1/pairing/complete", json={"displayCode": display_code}
        )
        token = complete_response.json()["token"]

        settings_response = clean_app.get(
            "/api/v1/settings", headers={"Authorization": f"Bearer {token}"}
        )
        assert settings_response.json()["exposureMode"] == "network"

    def test_update_exposure_mode_to_localhost_requires_auth(
        self, network_exposed_app: TestClient
    ) -> None:
        """Should reject exposureMode downgrade without authentication.

        Security: Downgrading from network → localhost requires auth to
        prevent remote clients from disabling network mode without auth.
        """
        response = network_exposed_app.post(
            "/api/v1/settings/exposure-mode", json={"exposureMode": "localhost"}
        )

        assert response.status_code == 401
        assert "authentication" in response.json()["detail"].lower()

    def test_update_exposure_mode_to_localhost_with_auth(
        self, network_exposed_app: TestClient
    ) -> None:
        """Should allow exposureMode downgrade with valid authentication."""
        # First, get a valid token
        start_response = network_exposed_app.post("/api/v1/pairing/start")
        display_code = start_response.json()["displayCode"]

        complete_response = network_exposed_app.post(
            "/api/v1/pairing/complete", json={"displayCode": display_code}
        )
        token = complete_response.json()["token"]

        # Now downgrade with auth
        response = network_exposed_app.post(
            "/api/v1/settings/exposure-mode",
            json={"exposureMode": "localhost"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["exposureMode"] == "localhost"

    def test_update_exposure_mode_invalid_value(self, clean_app: TestClient) -> None:
        """Should reject invalid exposureMode values."""
        response = clean_app.post(
            "/api/v1/settings/exposure-mode", json={"exposureMode": "invalid"}
        )

        assert response.status_code == 400


# =============================================================================
# T060: Auth Enforcement Tests
# =============================================================================


class TestAuthEnforcementInLocalhostMode:
    """Tests that auth is NOT required in localhost mode."""

    def test_settings_endpoint_no_auth_in_localhost(
        self, clean_app: TestClient
    ) -> None:
        """Should access settings without auth in localhost mode."""
        response = clean_app.get("/api/v1/settings")
        assert response.status_code == 200

    def test_projects_endpoint_no_auth_in_localhost(
        self, clean_app: TestClient
    ) -> None:
        """Should access projects without auth in localhost mode."""
        response = clean_app.get("/api/v1/projects")
        assert response.status_code == 200

    def test_health_endpoint_no_auth_in_localhost(self, clean_app: TestClient) -> None:
        """Should access health without auth in localhost mode."""
        response = clean_app.get("/api/v1/health")
        assert response.status_code == 200


class TestAuthEnforcementInNetworkMode:
    """Tests that auth IS required in network-exposed mode."""

    def test_settings_endpoint_accessible_without_auth_in_network_mode(
        self, network_exposed_app: TestClient
    ) -> None:
        """Settings endpoint should be accessible without auth for UI bootstrap."""
        # Settings must be readable without auth so the UI can show the pairing wizard
        response = network_exposed_app.get("/api/v1/settings")
        assert response.status_code == 200

    def test_projects_endpoint_requires_auth_in_network_mode(
        self, network_exposed_app: TestClient
    ) -> None:
        """Should reject projects request without auth in network mode."""
        response = network_exposed_app.get("/api/v1/projects")
        assert response.status_code == 401

    def test_health_endpoint_no_auth_required_even_in_network_mode(
        self, network_exposed_app: TestClient
    ) -> None:
        """Health endpoint should be accessible without auth (for monitoring)."""
        response = network_exposed_app.get("/api/v1/health")
        assert response.status_code == 200

    def test_pairing_start_no_auth_required_in_network_mode(
        self, network_exposed_app: TestClient
    ) -> None:
        """Pairing start endpoint should be accessible without auth."""
        response = network_exposed_app.post("/api/v1/pairing/start")
        # Should succeed (or fail for other reasons, not auth)
        assert response.status_code != 401

    def test_pairing_complete_no_auth_required_in_network_mode(
        self, network_exposed_app: TestClient
    ) -> None:
        """Pairing complete endpoint should be accessible without auth."""
        response = network_exposed_app.post(
            "/api/v1/pairing/complete", json={"displayCode": "ABC123"}
        )
        # Should fail with invalid code, not auth error
        assert response.status_code != 401


# =============================================================================
# T061: Pairing Service Tests
# =============================================================================


class TestPairingStart:
    """Tests for POST /pairing/start endpoint."""

    def test_pairing_start_returns_pairing_info(
        self, network_exposed_app: TestClient
    ) -> None:
        """Should return pairingId, displayCode, expiresAt, qrCodeDataUrl."""
        response = network_exposed_app.post("/api/v1/pairing/start")

        assert response.status_code == 200
        data = response.json()

        assert "pairingId" in data
        assert "displayCode" in data
        assert "expiresAt" in data
        assert "qrCodeDataUrl" in data

    def test_pairing_start_generates_unique_ids(
        self, network_exposed_app: TestClient
    ) -> None:
        """Should generate unique pairing IDs."""
        response1 = network_exposed_app.post("/api/v1/pairing/start")
        response2 = network_exposed_app.post("/api/v1/pairing/start")

        assert response1.json()["pairingId"] != response2.json()["pairingId"]

    def test_pairing_start_generates_readable_display_code(
        self, network_exposed_app: TestClient
    ) -> None:
        """Should generate a human-readable display code (6 chars, alphanumeric)."""
        response = network_exposed_app.post("/api/v1/pairing/start")
        data = response.json()

        display_code = data["displayCode"]
        assert len(display_code) == 6
        assert display_code.isalnum()
        assert display_code.isupper()  # Should be uppercase for readability

    def test_pairing_start_sets_expiration(
        self, network_exposed_app: TestClient
    ) -> None:
        """Should set expiration time (default 5 minutes)."""
        response = network_exposed_app.post("/api/v1/pairing/start")
        data = response.json()

        expires_at = datetime.fromisoformat(data["expiresAt"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)

        # Should expire in approximately 5 minutes (allow some tolerance)
        diff = (expires_at - now).total_seconds()
        assert 290 <= diff <= 310  # 5 minutes +/- 10 seconds

    def test_pairing_start_generates_qr_code(
        self, network_exposed_app: TestClient
    ) -> None:
        """Should generate a valid QR code data URL."""
        response = network_exposed_app.post("/api/v1/pairing/start")
        data = response.json()

        qr_url = data["qrCodeDataUrl"]
        assert qr_url.startswith("data:image/png;base64,")


class TestPairingComplete:
    """Tests for POST /pairing/complete endpoint."""

    def test_pairing_complete_with_valid_code(
        self, network_exposed_app: TestClient
    ) -> None:
        """Should complete pairing and return token."""
        # Start pairing first
        start_response = network_exposed_app.post("/api/v1/pairing/start")
        display_code = start_response.json()["displayCode"]

        # Complete pairing
        complete_response = network_exposed_app.post(
            "/api/v1/pairing/complete", json={"displayCode": display_code}
        )

        assert complete_response.status_code == 200
        data = complete_response.json()

        assert "token" in data
        assert "expiresAt" in data

    def test_pairing_complete_with_invalid_code(
        self, network_exposed_app: TestClient
    ) -> None:
        """Should reject invalid display codes."""
        response = network_exposed_app.post(
            "/api/v1/pairing/complete", json={"displayCode": "INVALID"}
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_pairing_complete_with_expired_code(
        self, network_exposed_app: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should reject expired display codes."""
        # Start pairing
        start_response = network_exposed_app.post("/api/v1/pairing/start")
        display_code = start_response.json()["displayCode"]

        # Mock time to be past expiration
        # We need to manually expire the pairing
        from services.pairing_service import get_pairing_service

        service = get_pairing_service()
        service._expire_all_pairings()  # Test helper to expire all pairings

        # Attempt complete
        complete_response = network_exposed_app.post(
            "/api/v1/pairing/complete", json={"displayCode": display_code}
        )

        assert complete_response.status_code == 400
        assert "expired" in complete_response.json()["detail"].lower()

    def test_pairing_complete_token_has_24h_expiry(
        self, network_exposed_app: TestClient
    ) -> None:
        """Should issue token with 24 hour expiry by default."""
        # Start and complete pairing
        start_response = network_exposed_app.post("/api/v1/pairing/start")
        display_code = start_response.json()["displayCode"]

        complete_response = network_exposed_app.post(
            "/api/v1/pairing/complete", json={"displayCode": display_code}
        )

        data = complete_response.json()
        expires_at = datetime.fromisoformat(data["expiresAt"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)

        # Should expire in approximately 24 hours
        diff = (expires_at - now).total_seconds()
        assert 86300 <= diff <= 86500  # 24 hours +/- 100 seconds

    def test_pairing_complete_code_is_consumed(
        self, network_exposed_app: TestClient
    ) -> None:
        """Should not allow reuse of display code."""
        # Start pairing
        start_response = network_exposed_app.post("/api/v1/pairing/start")
        display_code = start_response.json()["displayCode"]

        # Complete pairing first time
        complete_response1 = network_exposed_app.post(
            "/api/v1/pairing/complete", json={"displayCode": display_code}
        )
        assert complete_response1.status_code == 200

        # Try to complete again with same code
        complete_response2 = network_exposed_app.post(
            "/api/v1/pairing/complete", json={"displayCode": display_code}
        )
        assert complete_response2.status_code == 400


class TestPairingRevoke:
    """Tests for DELETE /pairing/{pairingId} endpoint."""

    def test_revoke_pairing_success(self, clean_app: TestClient) -> None:
        """Should revoke an active pairing in localhost mode."""
        # Start pairing
        start_response = clean_app.post("/api/v1/pairing/start")
        pairing_id = start_response.json()["pairingId"]

        # Revoke it
        revoke_response = clean_app.delete(f"/api/v1/pairing/{pairing_id}")

        assert revoke_response.status_code == 200

    def test_revoke_pairing_not_found(self, clean_app: TestClient) -> None:
        """Should return 404 for unknown pairing ID."""
        response = clean_app.delete("/api/v1/pairing/nonexistent")

        assert response.status_code == 404

    def test_revoked_pairing_cannot_be_completed(self, clean_app: TestClient) -> None:
        """Should not allow completing a revoked pairing."""
        # Start pairing
        start_response = clean_app.post("/api/v1/pairing/start")
        data = start_response.json()
        pairing_id = data["pairingId"]
        display_code = data["displayCode"]

        # Revoke it
        clean_app.delete(f"/api/v1/pairing/{pairing_id}")

        # Try to complete
        complete_response = clean_app.post(
            "/api/v1/pairing/complete", json={"displayCode": display_code}
        )

        assert complete_response.status_code == 400


class TestTokenValidation:
    """Tests for token validation in network mode."""

    def test_valid_token_grants_access(self, network_exposed_app: TestClient) -> None:
        """Should grant access with valid token."""
        # Start and complete pairing
        start_response = network_exposed_app.post("/api/v1/pairing/start")
        display_code = start_response.json()["displayCode"]

        complete_response = network_exposed_app.post(
            "/api/v1/pairing/complete", json={"displayCode": display_code}
        )
        token = complete_response.json()["token"]

        # Access protected endpoint with token
        settings_response = network_exposed_app.get(
            "/api/v1/settings", headers={"Authorization": f"Bearer {token}"}
        )

        assert settings_response.status_code == 200

    def test_invalid_token_denied(self, network_exposed_app: TestClient) -> None:
        """Should deny access with invalid token."""
        # Use projects endpoint since settings is now exempt from auth
        response = network_exposed_app.get(
            "/api/v1/projects", headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401

    def test_malformed_auth_header_denied(
        self, network_exposed_app: TestClient
    ) -> None:
        """Should deny access with malformed auth header."""
        # Use projects endpoint since settings is now exempt from auth
        response = network_exposed_app.get(
            "/api/v1/projects", headers={"Authorization": "NotBearer token"}
        )

        assert response.status_code == 401

    def test_revoke_token_denies_access(self, clean_app: TestClient) -> None:
        """Should deny access after token is revoked."""
        # First, switch to network mode
        clean_app.post(
            "/api/v1/settings/exposure-mode", json={"exposureMode": "network"}
        )

        # Start and complete pairing
        start_response = clean_app.post("/api/v1/pairing/start")
        data = start_response.json()
        display_code = data["displayCode"]

        complete_response = clean_app.post(
            "/api/v1/pairing/complete", json={"displayCode": display_code}
        )
        token = complete_response.json()["token"]

        # Verify token works (use projects endpoint since settings is exempt)
        projects_response1 = clean_app.get(
            "/api/v1/projects", headers={"Authorization": f"Bearer {token}"}
        )
        assert projects_response1.status_code == 200

        # Revoke via token endpoint
        revoke_response = clean_app.delete(
            "/api/v1/pairing/token", headers={"Authorization": f"Bearer {token}"}
        )
        assert revoke_response.status_code == 200

        # Token should no longer work
        projects_response2 = clean_app.get(
            "/api/v1/projects", headers={"Authorization": f"Bearer {token}"}
        )
        assert projects_response2.status_code == 401


class TestPairingList:
    """Tests for listing active pairings."""

    def test_list_active_pairings(self, network_exposed_app: TestClient) -> None:
        """Should list all active paired devices."""
        # Start and complete a pairing
        start_response = network_exposed_app.post("/api/v1/pairing/start")
        display_code = start_response.json()["displayCode"]

        complete_response = network_exposed_app.post(
            "/api/v1/pairing/complete", json={"displayCode": display_code}
        )
        token = complete_response.json()["token"]

        # List pairings (requires auth)
        list_response = network_exposed_app.get(
            "/api/v1/pairing", headers={"Authorization": f"Bearer {token}"}
        )

        assert list_response.status_code == 200
        data = list_response.json()

        assert "pairings" in data
        assert len(data["pairings"]) >= 1


class TestPairingStatus:
    """Tests for GET /pairing/{pairingId}/status endpoint."""

    def test_status_pending_before_complete(
        self, network_exposed_app: TestClient
    ) -> None:
        """Should return 'pending' status before pairing is completed."""
        # Start pairing
        start_response = network_exposed_app.post("/api/v1/pairing/start")
        data = start_response.json()
        pairing_id = data["pairingId"]

        # Check status - should be pending
        status_response = network_exposed_app.get(
            f"/api/v1/pairing/{pairing_id}/status"
        )

        assert status_response.status_code == 200
        status_data = status_response.json()

        assert status_data["pairingId"] == pairing_id
        assert status_data["status"] == "pending"
        assert status_data["completed"] is False
        assert "expiresAt" in status_data

    def test_status_completed_after_complete(
        self, network_exposed_app: TestClient
    ) -> None:
        """Should return 'completed' status after pairing is completed."""
        # Start pairing
        start_response = network_exposed_app.post("/api/v1/pairing/start")
        data = start_response.json()
        pairing_id = data["pairingId"]
        display_code = data["displayCode"]

        # Complete pairing
        network_exposed_app.post(
            "/api/v1/pairing/complete", json={"displayCode": display_code}
        )

        # Check status - should be completed
        status_response = network_exposed_app.get(
            f"/api/v1/pairing/{pairing_id}/status"
        )

        assert status_response.status_code == 200
        status_data = status_response.json()

        assert status_data["pairingId"] == pairing_id
        assert status_data["status"] == "completed"
        assert status_data["completed"] is True

    def test_status_revoked(self, clean_app: TestClient) -> None:
        """Should return 'revoked' status after pairing is revoked."""
        # Start pairing
        start_response = clean_app.post("/api/v1/pairing/start")
        data = start_response.json()
        pairing_id = data["pairingId"]

        # Revoke pairing
        clean_app.delete(f"/api/v1/pairing/{pairing_id}")

        # Check status - should be revoked
        status_response = clean_app.get(f"/api/v1/pairing/{pairing_id}/status")

        assert status_response.status_code == 200
        status_data = status_response.json()

        assert status_data["status"] == "revoked"

    def test_status_not_found(self, clean_app: TestClient) -> None:
        """Should return 404 for non-existent pairing."""
        status_response = clean_app.get("/api/v1/pairing/nonexistent-id/status")

        assert status_response.status_code == 404

    def test_status_accessible_without_auth_in_network_mode(
        self, network_exposed_app: TestClient
    ) -> None:
        """Status endpoint should be accessible without auth (for host UI polling)."""
        # Start pairing
        start_response = network_exposed_app.post("/api/v1/pairing/start")
        data = start_response.json()
        pairing_id = data["pairingId"]

        # Check status without auth - should work
        status_response = network_exposed_app.get(
            f"/api/v1/pairing/{pairing_id}/status"
        )

        # Should be 200, not 401
        assert status_response.status_code == 200
