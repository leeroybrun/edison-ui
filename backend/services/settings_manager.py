"""Settings manager service (T011).

Manages user settings including first-run setup and configuration updates.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class UserSettings:
    """User settings data structure."""

    scan_roots: list[str] = field(default_factory=list)
    display_name: str | None = None
    first_run_complete: bool = False
    exposure_mode: str = "localhost"
    realtime_enabled: bool = True
    realtime_watcher_enabled: bool = True
    realtime_polling_interval_ms: int = 5000


class SettingsManager:
    """Service for managing user settings."""

    ALLOWED_UPDATE_FIELDS = {"scanRoots", "displayName"}

    def __init__(self, settings_file: str | None = None) -> None:
        """Initialize the settings manager.

        Args:
            settings_file: Path to the settings JSON file.
                           Defaults to ~/.edison-ui/settings.json
        """
        if settings_file:
            self.settings_file = Path(settings_file).expanduser().resolve()
        else:
            self.settings_file = (
                Path("~/.edison-ui/settings.json").expanduser().resolve()
            )

        self._settings: UserSettings | None = None

    def _load(self) -> UserSettings:
        """Load settings from file."""
        if self._settings is not None:
            return self._settings

        if self.settings_file.exists():
            try:
                with open(self.settings_file) as f:
                    data = json.load(f)
                    self._settings = UserSettings(
                        scan_roots=data.get("scanRoots", []),
                        display_name=data.get("displayName"),
                        first_run_complete=data.get("firstRunComplete", False),
                        exposure_mode=data.get("exposureMode", "localhost"),
                        realtime_enabled=data.get("realtimeEnabled", True),
                        realtime_watcher_enabled=data.get(
                            "realtimeWatcherEnabled", True
                        ),
                        realtime_polling_interval_ms=data.get(
                            "realtimePollingIntervalMs", 5000
                        ),
                    )
            except (json.JSONDecodeError, OSError):
                self._settings = UserSettings()
        else:
            self._settings = UserSettings()

        return self._settings

    def _save(self) -> None:
        """Save settings to file."""
        if self._settings is None:
            return

        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "scanRoots": self._settings.scan_roots,
            "displayName": self._settings.display_name,
            "firstRunComplete": self._settings.first_run_complete,
            "exposureMode": self._settings.exposure_mode,
            "realtimeEnabled": self._settings.realtime_enabled,
            "realtimeWatcherEnabled": self._settings.realtime_watcher_enabled,
            "realtimePollingIntervalMs": self._settings.realtime_polling_interval_ms,
        }
        with open(self.settings_file, "w") as f:
            json.dump(data, f, indent=2)

    def get_settings(self) -> UserSettings:
        """Get current user settings."""
        return self._load()

    def needs_first_run_setup(self) -> bool:
        """Check if first-run setup is needed."""
        settings = self._load()
        return not settings.first_run_complete

    def get_suggested_scan_roots(self) -> list[str]:
        """Get suggested scan roots for first-run setup."""
        suggestions = []

        # Common project directories
        home = Path.home()
        candidates = [
            home / "projects",
            home / "Projects",
            home / "dev",
            home / "Development",
            home / "code",
            home / "src",
            home / "work",
            home / "Work",
        ]

        for candidate in candidates:
            if candidate.exists() and candidate.is_dir():
                suggestions.append(f"~/{candidate.name}")

        # If no common directories found, suggest ~/projects
        if not suggestions:
            suggestions.append("~/projects")

        return suggestions

    def validate_scan_roots(self, scan_roots: list[str]) -> list[str]:
        """Validate scan roots exist.

        Args:
            scan_roots: List of paths to validate.

        Returns:
            List of error messages (empty if all valid).
        """
        errors = []
        for root in scan_roots:
            expanded = Path(root).expanduser().resolve()
            if not expanded.exists():
                errors.append(f"Path does not exist: {root}")
            elif not expanded.is_dir():
                errors.append(f"Path is not a directory: {root}")
        return errors

    def complete_first_run(
        self,
        scan_roots: list[str],
        display_name: str | None = None,
    ) -> None:
        """Complete first-run setup.

        Args:
            scan_roots: List of directories to scan for projects.
            display_name: Optional display name for the user.

        Raises:
            ValueError: If scan_roots validation fails.
        """
        errors = self.validate_scan_roots(scan_roots)
        if errors:
            raise ValueError("; ".join(errors))

        settings = self._load()
        settings.scan_roots = scan_roots
        settings.display_name = display_name
        settings.first_run_complete = True
        self._save()

    def update_settings(
        self,
        scan_roots: list[str] | None = None,
        display_name: str | None = None,
    ) -> list[str]:
        """Update user settings.

        Args:
            scan_roots: New scan roots (optional).
            display_name: New display name (optional).

        Returns:
            List of field names that were updated.

        Raises:
            ValueError: If scan_roots validation fails.
        """
        updated = []
        settings = self._load()

        if scan_roots is not None:
            errors = self.validate_scan_roots(scan_roots)
            if errors:
                raise ValueError("; ".join(errors))
            settings.scan_roots = scan_roots
            updated.append("scanRoots")

        if display_name is not None:
            settings.display_name = display_name
            updated.append("displayName")

        if updated:
            self._save()

        return updated

    def is_field_allowed_for_update(self, field_name: str) -> bool:
        """Check if a field is allowed for PATCH updates."""
        return field_name in self.ALLOWED_UPDATE_FIELDS

    def get_os_user(self) -> str:
        """Get the current OS user."""
        return os.environ.get("USER", os.environ.get("USERNAME", "unknown"))
