"""Settings-related Pydantic schemas (T011)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RealtimeConfig(BaseModel):
    """Realtime configuration."""

    enabled: bool
    watcher_enabled: bool = Field(..., alias="watcherEnabled")
    polling_interval_ms: int = Field(..., alias="pollingIntervalMs")

    model_config = {"populate_by_name": True}


class ActorInfo(BaseModel):
    """Actor identity information."""

    os_user: str = Field(..., alias="osUser")
    display_name: str | None = Field(None, alias="displayName")

    model_config = {"populate_by_name": True}


class SettingsResponse(BaseModel):
    """Response for GET /settings endpoint."""

    scan_roots: list[str] = Field(..., alias="scanRoots")
    exposure_mode: str = Field(..., alias="exposureMode")
    realtime: RealtimeConfig
    actor: ActorInfo

    model_config = {"populate_by_name": True}


class SettingsUpdateRequest(BaseModel):
    """Request body for PATCH /settings endpoint."""

    scan_roots: list[str] | None = Field(None, alias="scanRoots")
    display_name: str | None = Field(None, alias="displayName")

    model_config = {"populate_by_name": True}


class SettingsUpdateResponse(BaseModel):
    """Response for PATCH /settings endpoint."""

    updated: list[str]
    audit_entry_id: str | None = Field(None, alias="auditEntryId")

    model_config = {"populate_by_name": True}


class FirstRunCheckResponse(BaseModel):
    """Response for GET /settings/first-run endpoint."""

    needs_setup: bool = Field(..., alias="needsSetup")
    suggested_roots: list[str] = Field(..., alias="suggestedRoots")

    model_config = {"populate_by_name": True}


class FirstRunRequest(BaseModel):
    """Request body for POST /settings/first-run endpoint."""

    scan_roots: list[str] = Field(..., alias="scanRoots")
    display_name: str | None = Field(None, alias="displayName")

    model_config = {"populate_by_name": True}
