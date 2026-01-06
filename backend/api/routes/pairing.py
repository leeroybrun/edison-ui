"""Pairing endpoints (T061).

Implements device pairing for remote mobile access.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Request

from api.schemas.pairing import (
    ExposureModeRequest,
    ExposureModeResponse,
    PairingCompleteRequest,
    PairingCompleteResponse,
    PairingInfo,
    PairingListResponse,
    PairingRevokeResponse,
    PairingStartResponse,
    PairingStatusResponse,
    TailscaleStatusResponse,
)
from services.network_info import get_pairing_base_url, get_tailscale_status
from services.pairing_service import get_pairing_service, reset_pairing_service
from services.settings_manager import SettingsManager

router = APIRouter(tags=["pairing"])


def get_settings_manager() -> SettingsManager:
    """Get a configured settings manager."""
    settings_file = os.environ.get("SETTINGS_FILE")
    return SettingsManager(settings_file=settings_file)


# =============================================================================
# Exposure Mode Endpoints
# =============================================================================


@router.post("/settings/exposure-mode", response_model=ExposureModeResponse)
async def update_exposure_mode(
    body: ExposureModeRequest, request: Request
) -> ExposureModeResponse:
    """Update the server exposure mode.

    This is a dedicated endpoint for changing exposure mode,
    separate from the general PATCH /settings for security.

    Security: Downgrading from network → localhost requires authentication
    to prevent remote clients from disabling network mode without auth.
    """
    valid_modes = ("localhost", "network", "tailscale")
    if body.exposure_mode not in valid_modes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid exposure mode: {body.exposure_mode}. Must be one of: {', '.join(valid_modes)}.",
        )

    # Check if tailscale is available when trying to enable it
    if body.exposure_mode == "tailscale":
        ts_status = get_tailscale_status()
        if not ts_status.running:
            raise HTTPException(
                status_code=400,
                detail="Tailscale is not running. Please start Tailscale and try again.",
            )

    manager = get_settings_manager()
    settings = manager.get_settings()

    # Security check: if currently in a remote-accessible mode and trying to downgrade,
    # require authentication (but allow from localhost without auth)
    is_remote_mode = settings.exposure_mode in ("network", "tailscale")
    is_downgrading = body.exposure_mode == "localhost"

    # Check if request is from localhost (no auth required for local access)
    client_host = request.client.host if request.client else None
    is_localhost = client_host in ("127.0.0.1", "::1", "localhost", None)

    if is_remote_mode and is_downgrading and not is_localhost:
        # Check for valid auth token (only required for remote requests)
        authorization = request.headers.get("authorization")
        token = None
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1]

        if token is None:
            raise HTTPException(
                status_code=401,
                detail="Authentication required to disable network mode from remote device.",
            )

        # Validate the token
        reset_pairing_service()
        pairing_service = get_pairing_service()
        if not pairing_service.validate_token(token):
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token.",
            )

    settings.exposure_mode = body.exposure_mode
    manager._settings = settings
    manager._save()

    return ExposureModeResponse(exposure_mode=body.exposure_mode)


@router.get("/settings/tailscale-status", response_model=TailscaleStatusResponse)
async def get_tailscale_availability() -> TailscaleStatusResponse:
    """Check if Tailscale is available on this system.

    Returns installation and running status for the frontend to
    conditionally show the Tailscale exposure mode option.
    """
    status = get_tailscale_status()
    return TailscaleStatusResponse(
        installed=status.installed,
        running=status.running,
        hostname=status.hostname,
        ip=status.ip,
    )


# =============================================================================
# Pairing Endpoints
# =============================================================================


@router.post("/pairing/start", response_model=PairingStartResponse)
async def start_pairing() -> PairingStartResponse:
    """Start a new pairing session.

    Returns a pairing ID, display code, expiration time, and QR code.
    The display code must be entered on the mobile device within 5 minutes.
    """
    # Reset singleton to pick up env changes (for tests)
    reset_pairing_service()
    service = get_pairing_service()

    # Get the current exposure mode to determine the correct base URL
    manager = get_settings_manager()
    settings = manager.get_settings()

    # Get frontend port from environment or default to 3000
    frontend_port = int(os.environ.get("FRONTEND_PORT", 3000))
    base_url = get_pairing_base_url(settings.exposure_mode, frontend_port)

    result = service.start_pairing(base_url=base_url)

    return PairingStartResponse(
        pairing_id=result["pairingId"],
        display_code=result["displayCode"],
        expires_at=result["expiresAt"],
        qr_code_data_url=result["qrCodeDataUrl"],
    )


@router.post("/pairing/complete", response_model=PairingCompleteResponse)
async def complete_pairing(body: PairingCompleteRequest) -> PairingCompleteResponse:
    """Complete a pairing using the display code.

    Returns a bearer token that can be used to authenticate API requests.
    """
    reset_pairing_service()
    service = get_pairing_service()

    try:
        result = service.complete_pairing(body.display_code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return PairingCompleteResponse(
        token=result["token"],
        expires_at=result["expiresAt"],
    )


@router.delete("/pairing/token")
async def revoke_token(request: Request) -> PairingRevokeResponse:
    """Revoke the current token.

    This invalidates only the specific token, not the entire pairing.
    """
    reset_pairing_service()
    service = get_pairing_service()

    # Get token from request state (set by middleware)
    token = getattr(request.state, "token", None)
    if token is None:
        # Try to extract from header directly for this endpoint
        authorization = request.headers.get("authorization")
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1]

    if token is None:
        raise HTTPException(status_code=401, detail="No token provided")

    if not service.revoke_token(token):
        raise HTTPException(status_code=404, detail="Token not found")

    return PairingRevokeResponse(revoked=True)


@router.get("/pairing/{pairing_id}/status", response_model=PairingStatusResponse)
async def get_pairing_status(pairing_id: str) -> PairingStatusResponse:
    """Get the status of a pairing session.

    Used by the host UI to poll and check if pairing was completed
    by a remote device.
    """
    reset_pairing_service()
    service = get_pairing_service()

    status = service.get_pairing_status(pairing_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Pairing not found")

    return PairingStatusResponse(
        pairing_id=status["pairingId"],
        status=status["status"],
        expires_at=status["expiresAt"],
        completed=status["completed"],
    )


@router.delete("/pairing/{pairing_id}", response_model=PairingRevokeResponse)
async def revoke_pairing(pairing_id: str) -> PairingRevokeResponse:
    """Revoke a pairing session.

    This invalidates the pairing and any associated tokens.
    """
    reset_pairing_service()
    service = get_pairing_service()

    if not service.revoke_pairing(pairing_id):
        raise HTTPException(status_code=404, detail="Pairing not found")

    return PairingRevokeResponse(revoked=True)


@router.get("/pairing", response_model=PairingListResponse)
async def list_pairings() -> PairingListResponse:
    """List all active paired devices.

    Returns information about paired devices without exposing tokens.
    """
    reset_pairing_service()
    service = get_pairing_service()
    pairings_raw = service.list_pairings()

    # Convert dict to PairingInfo
    pairings = [
        PairingInfo(
            pairing_id=p["pairingId"],
            created_at=p["createdAt"],
            expires_at=p["expiresAt"],
            last_used=p.get("lastUsed"),
        )
        for p in pairings_raw
    ]

    return PairingListResponse(pairings=pairings)
