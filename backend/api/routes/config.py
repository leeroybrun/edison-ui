"""Config endpoints (T076).

Implements pack and configuration management with allowlist-based safety.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas.config import (
    ConfigApplyRequest,
    ConfigApplyResponse,
    ConfigPreview,
    ConfigPreviewRequest,
    ConfigPreviewResponse,
    PackDetail,
    PackListItem,
    PackListResponse,
    ProjectConfigResponse,
)
from core.settings import get_settings
from services.config_service import ConfigService
from services.project_discovery import ProjectDiscoveryService

router = APIRouter(prefix="/projects/{project_id}", tags=["config"])


def get_discovery_service() -> ProjectDiscoveryService:
    """Get a configured project discovery service."""
    settings = get_settings()
    return ProjectDiscoveryService(
        scan_roots=settings.get_expanded_scan_roots(),
        ignore_patterns=settings.scan_ignore_patterns,
        pin_storage_path=settings.get_expanded_pin_storage_path(),
    )


def get_project_path(project_id: str) -> str:
    """Get the project path from project ID.

    Args:
        project_id: The project ID.

    Returns:
        The project path.

    Raises:
        HTTPException: If project not found.
    """
    service = get_discovery_service()
    project = service.get_project_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project.path


@router.get("/config", response_model=ProjectConfigResponse)
async def get_project_config(project_id: str) -> ProjectConfigResponse:
    """Get project configuration.

    Returns the current configuration including active packs and settings.
    """
    project_path = get_project_path(project_id)
    config_service = ConfigService(project_path)

    try:
        config = config_service.get_project_config()
        active_packs = config_service.get_active_packs()
    except ValueError:
        raise HTTPException(
            status_code=500,
            detail="Configuration file is malformed",
        )

    return ProjectConfigResponse(
        project_id=project_id,
        active_packs=active_packs,
        config=config,
    )


@router.get("/packs", response_model=PackListResponse)
async def list_packs(project_id: str) -> PackListResponse:
    """List available packs for the project.

    Returns all packs discovered in the project's .edison/packs directory.
    """
    project_path = get_project_path(project_id)
    config_service = ConfigService(project_path)

    packs = config_service.list_packs()
    items = [
        PackListItem(
            pack_id=p.pack_id,
            name=p.name,
            description=p.description,
            enabled=p.enabled,
            source=p.source,
        )
        for p in packs
    ]

    return PackListResponse(items=items, total=len(items))


@router.get("/packs/{pack_id}", response_model=PackDetail)
async def get_pack_detail(project_id: str, pack_id: str) -> PackDetail:
    """Get detailed information about a specific pack.

    Args:
        project_id: The project identifier.
        pack_id: The pack identifier.

    Returns:
        Detailed pack information including configuration.
    """
    project_path = get_project_path(project_id)
    config_service = ConfigService(project_path)

    pack = config_service.get_pack(pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail=f"Pack {pack_id} not found")

    return PackDetail(
        pack_id=pack.pack_id,
        name=pack.name,
        description=pack.description,
        enabled=pack.enabled,
        config=config_service.redact_pack_config(pack.config),
        source=pack.source,
    )


@router.post("/config/preview", response_model=ConfigPreviewResponse)
async def preview_config_change(
    project_id: str, request: ConfigPreviewRequest
) -> ConfigPreviewResponse:
    """Preview a configuration change before applying.

    Validates the field is in the edit allowlist and returns
    current vs new values for user confirmation.
    """
    project_path = get_project_path(project_id)
    config_service = ConfigService(project_path)

    result = config_service.preview_change(request.field, request.value)

    preview = None
    if result.valid:
        preview = ConfigPreview(
            field=result.field,
            current_value=result.current_value,
            new_value=result.new_value,
        )

    return ConfigPreviewResponse(
        valid=result.valid,
        preview=preview,
        warnings=result.warnings,
        reason=result.reason,
    )


@router.post("/config", response_model=ConfigApplyResponse)
async def apply_config_change(
    project_id: str, request: ConfigApplyRequest
) -> ConfigApplyResponse:
    """Apply a configuration change.

    Requires confirmed=true and the field must be in the edit allowlist.
    Creates a backup before making changes.
    """
    project_path = get_project_path(project_id)
    config_service = ConfigService(project_path)

    # Check allowlist first for disallowed fields - return 400
    if not config_service.is_field_allowed(request.field):
        raise HTTPException(
            status_code=400,
            detail=f"Field '{request.field}' is not editable via the API",
        )

    result = config_service.apply_change(
        request.field, request.value, request.confirmed
    )

    return ConfigApplyResponse(
        success=result.success,
        audit_entry_id=result.audit_entry_id,
        backup_path=result.backup_path,
        reason=result.reason,
    )
