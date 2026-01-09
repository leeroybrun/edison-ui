"""Tests for network info helpers.

These utilities are used for pairing URL generation and must gracefully handle
missing/failed system dependencies (e.g., tailscale CLI).
"""

from __future__ import annotations

import pytest

from services import network_info


def test_get_tailscale_status_handles_oserror_without_nameerror(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Should return a non-running status when the tailscale CLI call errors."""

    def fake_which(_command: str) -> str:
        return "/usr/bin/tailscale"

    monkeypatch.setattr(network_info.shutil, "which", fake_which)

    def raise_oserror(*_args: object, **_kwargs: object) -> None:
        raise OSError("boom")

    monkeypatch.setattr(network_info.subprocess, "run", raise_oserror)

    status = network_info.get_tailscale_status()

    assert status.installed is True
    assert status.running is False
