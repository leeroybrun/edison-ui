"""Services package for Edison UI backend.

Exports core services for audit logging, project discovery, and settings.
"""

from __future__ import annotations

from services.audit import AuditWriter, FilesystemConfinementError, redact_context
from services.project_discovery import (
    DiscoveredProject,
    ProjectDiscoveryService,
    ProjectHealth,
)
from services.settings_manager import SettingsManager, UserSettings

__all__ = [
    # Audit services
    "AuditWriter",
    "FilesystemConfinementError",
    "redact_context",
    # Project discovery services
    "ProjectDiscoveryService",
    "DiscoveredProject",
    "ProjectHealth",
    # Settings services
    "SettingsManager",
    "UserSettings",
]
