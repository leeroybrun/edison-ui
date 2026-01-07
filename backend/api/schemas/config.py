"""Schemas for pack/config endpoints (T076)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProjectConfigResponse(BaseModel):
    """Response for GET /projects/{projectId}/config."""

    project_id: str = Field(alias="projectId")
    active_packs: list[str] = Field(alias="activePacks")
    config: dict[str, Any]

    model_config = {"populate_by_name": True}


class PackListItem(BaseModel):
    """Single item in pack list response."""

    pack_id: str = Field(alias="packId")
    name: str
    description: str | None = None
    enabled: bool
    source: str  # "core" or "project"

    model_config = {"populate_by_name": True}


class PackListResponse(BaseModel):
    """Response for GET /projects/{projectId}/packs."""

    items: list[PackListItem]
    total: int


class PackDetail(BaseModel):
    """Response for GET /projects/{projectId}/packs/{packId}."""

    pack_id: str = Field(alias="packId")
    name: str
    description: str | None = None
    enabled: bool
    config: dict[str, Any] | None = None
    source: str

    model_config = {"populate_by_name": True}


class ConfigPreviewRequest(BaseModel):
    """Request for POST /projects/{projectId}/config/preview."""

    field: str
    value: Any


class ConfigPreview(BaseModel):
    """Preview of a config change."""

    field: str
    current_value: Any = Field(alias="currentValue")
    new_value: Any = Field(alias="newValue")

    model_config = {"populate_by_name": True}


class ConfigPreviewResponse(BaseModel):
    """Response for POST /projects/{projectId}/config/preview."""

    valid: bool
    preview: ConfigPreview | None = None
    warnings: list[str] = Field(default_factory=list)
    reason: str | None = None


class ConfigApplyRequest(BaseModel):
    """Request for POST /projects/{projectId}/config."""

    field: str
    value: Any
    confirmed: bool = False


class ConfigApplyResponse(BaseModel):
    """Response for POST /projects/{projectId}/config."""

    success: bool
    audit_entry_id: str | None = Field(alias="auditEntryId", default=None)
    backup_path: str | None = Field(alias="backupPath", default=None)
    reason: str | None = None

    model_config = {"populate_by_name": True}
