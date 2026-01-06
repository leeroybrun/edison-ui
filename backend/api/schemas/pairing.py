"""Pairing-related Pydantic schemas (T061)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExposureModeRequest(BaseModel):
    """Request body for POST /settings/exposure-mode."""

    exposure_mode: str = Field(..., alias="exposureMode")

    model_config = {"populate_by_name": True}


class ExposureModeResponse(BaseModel):
    """Response for POST /settings/exposure-mode."""

    exposure_mode: str = Field(..., alias="exposureMode")

    model_config = {"populate_by_name": True}


class PairingStartResponse(BaseModel):
    """Response for POST /pairing/start."""

    pairing_id: str = Field(..., alias="pairingId")
    display_code: str = Field(..., alias="displayCode")
    expires_at: str = Field(..., alias="expiresAt")
    qr_code_data_url: str = Field(..., alias="qrCodeDataUrl")

    model_config = {"populate_by_name": True}


class PairingCompleteRequest(BaseModel):
    """Request body for POST /pairing/complete."""

    display_code: str = Field(..., alias="displayCode")

    model_config = {"populate_by_name": True}


class PairingCompleteResponse(BaseModel):
    """Response for POST /pairing/complete."""

    token: str
    expires_at: str = Field(..., alias="expiresAt")

    model_config = {"populate_by_name": True}


class PairingRevokeResponse(BaseModel):
    """Response for DELETE /pairing/{pairingId}."""

    revoked: bool


class PairingInfo(BaseModel):
    """Information about an active pairing."""

    pairing_id: str = Field(..., alias="pairingId")
    created_at: str = Field(..., alias="createdAt")
    expires_at: str = Field(..., alias="expiresAt")
    last_used: str | None = Field(None, alias="lastUsed")

    model_config = {"populate_by_name": True}


class PairingListResponse(BaseModel):
    """Response for GET /pairing."""

    pairings: list[PairingInfo]


class PairingStatusResponse(BaseModel):
    """Response for GET /pairing/{pairingId}/status."""

    pairing_id: str = Field(..., alias="pairingId")
    status: str = Field(
        ..., description="pending | completed | expired | revoked"
    )
    expires_at: str = Field(..., alias="expiresAt")
    completed: bool

    model_config = {"populate_by_name": True}


class TailscaleStatusResponse(BaseModel):
    """Response for GET /settings/tailscale-status."""

    installed: bool
    running: bool
    hostname: str | None = None
    ip: str | None = None

    model_config = {"populate_by_name": True}
