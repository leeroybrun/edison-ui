"""Config service for pack/config endpoints (T076).

Manages reading and editing project configuration with allowlist-based safety.
"""

from __future__ import annotations

import logging
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


# Fields that are allowed to be edited via the API
ALLOWED_FIELDS = {
    "scanRoots",
    "displayName",
    "exposureMode",
    "realtime.pollingIntervalMs",
}

# Fields that are explicitly disallowed (for documentation and clearer errors)
DISALLOWED_FIELDS = {
    "constitutions",
    "credentials",
    "apiKeys",
    "secrets",
}

# Fields that should be redacted from config responses (security sensitive)
REDACTED_FIELDS = {
    "credentials",
    "apiKeys",
    "secrets",
    "tokens",
    "passwords",
    "privateKeys",
}


@dataclass
class Pack:
    """Represents a configuration pack."""

    pack_id: str
    name: str
    description: str | None
    enabled: bool
    config: dict[str, Any] | None
    source: str  # "core" or "project"


@dataclass
class ConfigPreviewResult:
    """Result of previewing a config change."""

    valid: bool
    field: str
    current_value: Any
    new_value: Any
    warnings: list[str]
    reason: str | None


@dataclass
class ConfigApplyResult:
    """Result of applying a config change."""

    success: bool
    audit_entry_id: str | None
    backup_path: str | None
    reason: str | None


class ConfigService:
    """Service for managing project configuration."""

    def __init__(self, project_path: str) -> None:
        """Initialize the config service.

        Args:
            project_path: Path to the project root.
        """
        self.project_path = Path(project_path)
        self.edison_dir = self.project_path / ".edison"
        self.config_dir = self.edison_dir / "config"
        self.packs_dir = self.edison_dir / "packs"
        self.config_file = self.config_dir / "project.yaml"

    def get_project_config(self) -> dict[str, Any]:
        """Get the project configuration (safe for API responses).

        Returns:
            Dictionary of configuration values with sensitive fields redacted.
        """
        config = self._get_raw_config()
        return self._redact_sensitive_fields(config)

    def _get_raw_config(self) -> dict[str, Any]:
        """Get raw project configuration (for internal use only).

        Returns:
            Dictionary of configuration values without redaction.

        Raises:
            ValueError: If config file is malformed.
        """
        if not self.config_file.exists():
            return {}

        try:
            content = self.config_file.read_text()
            config = yaml.safe_load(content)
            if config is None:
                return {}
            if not isinstance(config, dict):
                logger.error("Config file is not a valid YAML dictionary: %s", self.config_file)
                raise ValueError("Config file is malformed")
            return config
        except yaml.YAMLError as e:
            logger.error("Failed to parse config file %s: %s", self.config_file, e)
            raise ValueError(f"Failed to parse config: {e}") from e

    def _redact_sensitive_fields(self, config: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive fields from config to prevent secret exposure.

        Args:
            config: The configuration dictionary.

        Returns:
            Configuration with sensitive fields replaced with "[REDACTED]".
        """
        result: dict[str, Any] = {}
        for key, value in config.items():
            if key in REDACTED_FIELDS:
                result[key] = "[REDACTED]"
            elif isinstance(value, dict):
                result[key] = self._redact_sensitive_fields(value)
            elif isinstance(value, list):
                result[key] = self._redact_list(value)
            else:
                result[key] = value
        return result

    def _redact_list(self, items: list[Any]) -> list[Any]:
        """Redact sensitive fields in list items.

        Args:
            items: List that may contain dicts with sensitive fields.

        Returns:
            List with sensitive fields redacted in any dict items.
        """
        result: list[Any] = []
        for item in items:
            if isinstance(item, dict):
                result.append(self._redact_sensitive_fields(item))
            elif isinstance(item, list):
                result.append(self._redact_list(item))
            else:
                result.append(item)
        return result

    def redact_pack_config(self, config: dict[str, Any] | None) -> dict[str, Any] | None:
        """Redact sensitive fields from pack config for API responses.

        Args:
            config: The pack configuration dictionary.

        Returns:
            Configuration with sensitive fields redacted, or None if input is None.
        """
        if config is None:
            return None
        return self._redact_sensitive_fields(config)

    def get_active_packs(self) -> list[str]:
        """Get list of active pack IDs.

        Returns:
            List of enabled pack IDs.
        """
        packs = self.list_packs()
        return [p.pack_id for p in packs if p.enabled]

    def list_packs(self) -> list[Pack]:
        """List all available packs.

        Returns:
            List of Pack objects.
        """
        packs: list[Pack] = []

        if not self.packs_dir.exists():
            return packs

        for pack_path in self.packs_dir.iterdir():
            if not pack_path.is_dir():
                continue

            # Skip pack directories with dots in name (consistent with get_pack)
            if "." in pack_path.name:
                continue

            # Prevent symlink escape - ensure resolved path is within packs_dir
            try:
                pack_path.resolve().relative_to(self.packs_dir.resolve())
            except ValueError:
                continue

            pack_yaml = pack_path / "pack.yaml"
            if not pack_yaml.exists():
                continue

            try:
                content = yaml.safe_load(pack_yaml.read_text()) or {}
                packs.append(
                    Pack(
                        pack_id=pack_path.name,
                        name=content.get("name", pack_path.name),
                        description=content.get("description"),
                        enabled=content.get("enabled", True),
                        config=content.get("config"),
                        source="project",  # All packs in .edison/packs are project-level
                    )
                )
            except Exception:
                continue

        return packs

    def get_pack(self, pack_id: str) -> Pack | None:
        """Get a specific pack by ID.

        Args:
            pack_id: The pack identifier.

        Returns:
            Pack object if found, None otherwise.
        """
        # Prevent path traversal attacks - reject /, \, and any dots
        if "/" in pack_id or "\\" in pack_id or "." in pack_id:
            return None

        pack_path = self.packs_dir / pack_id

        # Verify the resolved path is still within packs_dir
        try:
            pack_path.resolve().relative_to(self.packs_dir.resolve())
        except ValueError:
            return None

        if not pack_path.is_dir():
            return None

        pack_yaml = pack_path / "pack.yaml"
        if not pack_yaml.exists():
            return None

        try:
            content = yaml.safe_load(pack_yaml.read_text()) or {}
            return Pack(
                pack_id=pack_id,
                name=content.get("name", pack_id),
                description=content.get("description"),
                enabled=content.get("enabled", True),
                config=content.get("config"),
                source="project",
            )
        except Exception:
            return None

    def is_field_allowed(self, field: str) -> bool:
        """Check if a field is in the edit allowlist.

        Args:
            field: The field path (dot-separated for nested fields).

        Returns:
            True if field is allowed to be edited.
        """
        # Check exact match
        if field in ALLOWED_FIELDS:
            return True

        # Check if field starts with any disallowed prefix
        for disallowed in DISALLOWED_FIELDS:
            if field.startswith(disallowed):
                return False

        # Check for pack config changes (disallowed)
        if field.startswith("packs."):
            return False

        return False

    def get_nested_value(self, config: dict[str, Any], field: str) -> Any:
        """Get a nested value from config using dot notation.

        Args:
            config: The configuration dictionary.
            field: Dot-separated field path.

        Returns:
            The value at the path, or None if not found.
        """
        parts = field.split(".")
        current = config

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def set_nested_value(
        self, config: dict[str, Any], field: str, value: Any
    ) -> dict[str, Any]:
        """Set a nested value in config using dot notation.

        Args:
            config: The configuration dictionary.
            field: Dot-separated field path.
            value: The value to set.

        Returns:
            Updated configuration dictionary.
        """
        parts = field.split(".")
        current = config

        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value
        return config

    def preview_change(self, field: str, value: Any) -> ConfigPreviewResult:
        """Preview a configuration change.

        Args:
            field: The field to change.
            value: The new value.

        Returns:
            ConfigPreviewResult with validation info.
        """
        warnings: list[str] = []

        # Check allowlist
        if not self.is_field_allowed(field):
            return ConfigPreviewResult(
                valid=False,
                field=field,
                current_value=None,
                new_value=value,
                warnings=[],
                reason=f"Field '{field}' is not editable via the API",
            )

        # Get current config and value (use raw config to get actual values)
        try:
            config = self._get_raw_config()
        except ValueError:
            config = {}
        current_value = self.get_nested_value(config, field)

        # Add warnings for sensitive changes
        if field == "exposureMode" and value == "network":
            warnings.append(
                "Changing to network mode will require device pairing for access"
            )

        return ConfigPreviewResult(
            valid=True,
            field=field,
            current_value=current_value,
            new_value=value,
            warnings=warnings,
            reason=None,
        )

    def apply_change(
        self, field: str, value: Any, confirmed: bool
    ) -> ConfigApplyResult:
        """Apply a configuration change.

        Args:
            field: The field to change.
            value: The new value.
            confirmed: Whether the user confirmed the change.

        Returns:
            ConfigApplyResult with outcome info.
        """
        # Require confirmation
        if not confirmed:
            return ConfigApplyResult(
                success=False,
                audit_entry_id=None,
                backup_path=None,
                reason="Change must be confirmed with confirmed=true",
            )

        # Check allowlist
        if not self.is_field_allowed(field):
            return ConfigApplyResult(
                success=False,
                audit_entry_id=None,
                backup_path=None,
                reason=f"Field '{field}' is not editable via the API",
            )

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Create backup
        backup_path = self._create_backup()

        try:
            # Update config - use raw config to preserve all fields
            config = self._get_raw_config()
            config = self.set_nested_value(config, field, value)

            # Write updated config using safe_dump
            self.config_file.write_text(yaml.safe_dump(config, default_flow_style=False))

            # Generate audit entry ID
            audit_entry_id = f"audit-{uuid.uuid4().hex[:8]}"

            return ConfigApplyResult(
                success=True,
                audit_entry_id=audit_entry_id,
                backup_path=str(backup_path) if backup_path else None,
                reason=None,
            )
        except ValueError as e:
            logger.error("Failed to apply config change: %s", e)
            return ConfigApplyResult(
                success=False,
                audit_entry_id=None,
                backup_path=str(backup_path) if backup_path else None,
                reason=f"Failed to update config: {e}",
            )
        except Exception as e:
            logger.error("Unexpected error applying config change: %s", e)
            return ConfigApplyResult(
                success=False,
                audit_entry_id=None,
                backup_path=str(backup_path) if backup_path else None,
                reason="An unexpected error occurred while updating config",
            )

    def _create_backup(self) -> Path | None:
        """Create a backup of the current config.

        Returns:
            Path to backup file, or None if no config exists.
        """
        if not self.config_file.exists():
            return None

        backup_dir = self.edison_dir / ".config-backup"
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        backup_path = backup_dir / f"{timestamp}.yaml"

        shutil.copy(self.config_file, backup_path)
        return backup_path
