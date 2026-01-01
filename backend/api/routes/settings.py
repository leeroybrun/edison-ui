"""Settings endpoints (T011).

Implements settings retrieval, update, and first-run setup endpoints.
"""
from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from api.schemas.settings import (
    ActorInfo,
    FirstRunCheckResponse,
    FirstRunRequest,
    RealtimeConfig,
    SettingsResponse,
    SettingsUpdateRequest,
    SettingsUpdateResponse,
)
from services.settings_manager import SettingsManager

router = APIRouter(prefix="/settings", tags=["settings"])


def get_settings_manager() -> SettingsManager:
    """Get a configured settings manager."""
    # Use SETTINGS_FILE env var if available, otherwise default
    settings_file = os.environ.get("SETTINGS_FILE")
    return SettingsManager(settings_file=settings_file)


@router.get("", response_model=SettingsResponse)
async def get_current_settings() -> SettingsResponse:
    """Get current user settings."""
    manager = get_settings_manager()
    user_settings = manager.get_settings()

    return SettingsResponse(
        scan_roots=user_settings.scan_roots,
        exposure_mode=user_settings.exposure_mode,
        realtime=RealtimeConfig(
            enabled=user_settings.realtime_enabled,
            watcher_enabled=user_settings.realtime_watcher_enabled,
            polling_interval_ms=user_settings.realtime_polling_interval_ms,
        ),
        actor=ActorInfo(
            os_user=manager.get_os_user(),
            display_name=user_settings.display_name,
        ),
    )


@router.patch("", response_model=SettingsUpdateResponse)
async def update_settings(body: SettingsUpdateRequest) -> SettingsUpdateResponse:
    """Update user settings (allowlisted fields only)."""
    manager = get_settings_manager()

    # Check for disallowed fields in the request
    request_data = body.model_dump(exclude_none=True, by_alias=True)
    for field_name in request_data:
        if not manager.is_field_allowed_for_update(field_name):
            raise HTTPException(
                status_code=400,
                detail=f"Field '{field_name}' is not allowed for update via PATCH"
            )

    try:
        updated = manager.update_settings(
            scan_roots=body.scan_roots,
            display_name=body.display_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return SettingsUpdateResponse(
        updated=updated,
        audit_entry_id=None,  # TODO: Add audit integration
    )


@router.get("/first-run", response_model=FirstRunCheckResponse)
async def check_first_run() -> FirstRunCheckResponse:
    """Check if first-run setup is needed."""
    manager = get_settings_manager()

    return FirstRunCheckResponse(
        needs_setup=manager.needs_first_run_setup(),
        suggested_roots=manager.get_suggested_scan_roots(),
    )


@router.post("/first-run", response_model=SettingsUpdateResponse)
async def complete_first_run(body: FirstRunRequest) -> SettingsUpdateResponse:
    """Complete first-run setup."""
    manager = get_settings_manager()

    try:
        manager.complete_first_run(
            scan_roots=body.scan_roots,
            display_name=body.display_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    updated = ["scanRoots", "firstRunComplete"]
    if body.display_name:
        updated.append("displayName")

    return SettingsUpdateResponse(
        updated=updated,
        audit_entry_id=None,  # TODO: Add audit integration
    )
