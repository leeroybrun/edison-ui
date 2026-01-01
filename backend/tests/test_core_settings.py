"""TDD tests for project discovery settings configuration (T006).

RED Phase: Tests written first, expected to fail until implementation.
"""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from core.settings import Settings


class TestScanRootsConfig:
    """Test scan_roots configuration for project discovery."""

    def test_scan_roots_default_value(self) -> None:
        """scan_roots should default to ['~/projects']."""
        settings = Settings()
        assert settings.scan_roots == ["~/projects"]

    def test_scan_roots_from_env_single_path(self) -> None:
        """scan_roots should load from SCAN_ROOTS env var."""
        with patch.dict(os.environ, {"SCAN_ROOTS": "~/dev"}, clear=True):
            settings = Settings()
            assert settings.scan_roots == ["~/dev"]

    def test_scan_roots_from_env_multiple_paths(self) -> None:
        """scan_roots should support comma-separated paths in SCAN_ROOTS."""
        with patch.dict(os.environ, {"SCAN_ROOTS": "~/dev,~/projects,~/work"}, clear=True):
            settings = Settings()
            assert settings.scan_roots == ["~/dev", "~/projects", "~/work"]

    def test_scan_roots_tilde_expansion(self) -> None:
        """scan_roots paths should expand ~ to home directory."""
        settings = Settings()
        expanded = settings.get_expanded_scan_roots()
        for path in expanded:
            assert not path.startswith("~"), f"Path {path} was not expanded"
            assert Path(path).is_absolute(), f"Path {path} is not absolute"

    def test_scan_roots_expansion_preserves_order(self) -> None:
        """Expanded scan_roots should preserve the original order."""
        with patch.dict(os.environ, {"SCAN_ROOTS": "~/a,~/b,~/c"}, clear=True):
            settings = Settings()
            expanded = settings.get_expanded_scan_roots()
            home = str(Path.home())
            assert expanded == [f"{home}/a", f"{home}/b", f"{home}/c"]


class TestScanIgnorePatternsConfig:
    """Test scan_ignore_patterns configuration."""

    def test_scan_ignore_patterns_default_value(self) -> None:
        """scan_ignore_patterns should have sensible defaults."""
        settings = Settings()
        expected_defaults = ["node_modules", ".git", ".venv", "__pycache__"]
        assert settings.scan_ignore_patterns == expected_defaults

    def test_scan_ignore_patterns_from_env(self) -> None:
        """scan_ignore_patterns should load from SCAN_IGNORE_PATTERNS env var."""
        with patch.dict(
            os.environ, {"SCAN_IGNORE_PATTERNS": ".git,dist,build"}, clear=True
        ):
            settings = Settings()
            assert settings.scan_ignore_patterns == [".git", "dist", "build"]

    def test_scan_ignore_patterns_empty_list(self) -> None:
        """Empty SCAN_IGNORE_PATTERNS should result in empty list."""
        with patch.dict(os.environ, {"SCAN_IGNORE_PATTERNS": ""}, clear=True):
            settings = Settings()
            assert settings.scan_ignore_patterns == []


class TestPinStoragePathConfig:
    """Test pin_storage_path configuration."""

    def test_pin_storage_path_default_value(self) -> None:
        """pin_storage_path should default to ~/.edison-ui/pins.json."""
        settings = Settings()
        assert settings.pin_storage_path == "~/.edison-ui/pins.json"

    def test_pin_storage_path_from_env(self) -> None:
        """pin_storage_path should load from PIN_STORAGE_PATH env var."""
        with patch.dict(os.environ, {"PIN_STORAGE_PATH": "/custom/pins.json"}):
            settings = Settings()
            assert settings.pin_storage_path == "/custom/pins.json"

    def test_pin_storage_path_can_be_none(self) -> None:
        """pin_storage_path should support None value (no pinning)."""
        with patch.dict(os.environ, {"PIN_STORAGE_PATH": ""}):
            settings = Settings()
            # Empty string should be treated as None/disabled
            assert settings.pin_storage_path == "" or settings.pin_storage_path is None

    def test_get_expanded_pin_storage_path(self) -> None:
        """get_expanded_pin_storage_path should expand tilde."""
        settings = Settings()
        expanded = settings.get_expanded_pin_storage_path()
        assert expanded is not None
        assert not expanded.startswith("~")
        assert Path(expanded).is_absolute()
        assert expanded.endswith("pins.json")


class TestExistingSettingsPreserved:
    """Ensure existing settings still work after adding new fields."""

    def test_api_host_still_works(self) -> None:
        """api_host should still have default and be configurable."""
        settings = Settings()
        assert settings.api_host == "0.0.0.0"

    def test_api_port_still_works(self) -> None:
        """api_port should still have default and be configurable."""
        settings = Settings()
        assert settings.api_port == 8000

    def test_cors_origins_still_works(self) -> None:
        """cors_origins should still have default and be configurable."""
        settings = Settings()
        assert "http://localhost:3000" in settings.cors_origins

    def test_edison_path_still_works(self) -> None:
        """edison_path should still be accessible."""
        settings = Settings()
        assert hasattr(settings, "edison_path")

    def test_edison_projects_root_still_works(self) -> None:
        """edison_projects_root should still be accessible."""
        settings = Settings()
        assert hasattr(settings, "edison_projects_root")
