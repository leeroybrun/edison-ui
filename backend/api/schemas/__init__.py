"""API schemas package.

Exports all shared schema models for errors, guards, projects, and settings.
"""

from __future__ import annotations

from api.schemas.errors import ErrorDetail, ErrorResponse, ValidationErrorResponse
from api.schemas.guards import (
    GuardApplyResponse,
    GuardCheckResult,
    GuardPreviewResponse,
)
from api.schemas.projects import (
    PinRequest,
    PinResponse,
    ProjectConfig,
    ProjectDetail,
    ProjectHealth,
    ProjectListItem,
    ProjectListResponse,
)
from api.schemas.settings import (
    ActorInfo,
    FirstRunCheckResponse,
    FirstRunRequest,
    RealtimeConfig,
    SettingsResponse,
    SettingsUpdateRequest,
    SettingsUpdateResponse,
)

__all__ = [
    # Error schemas
    "ErrorDetail",
    "ErrorResponse",
    "ValidationErrorResponse",
    # Guard schemas
    "GuardCheckResult",
    "GuardPreviewResponse",
    "GuardApplyResponse",
    # Project schemas
    "ProjectHealth",
    "ProjectListItem",
    "ProjectListResponse",
    "ProjectConfig",
    "ProjectDetail",
    "PinRequest",
    "PinResponse",
    # Settings schemas
    "RealtimeConfig",
    "ActorInfo",
    "SettingsResponse",
    "SettingsUpdateRequest",
    "SettingsUpdateResponse",
    "FirstRunCheckResponse",
    "FirstRunRequest",
]
