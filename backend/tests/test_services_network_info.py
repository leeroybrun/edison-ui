"""Tests for network info helpers.

These utilities are used for pairing URL generation and must gracefully handle
missing/failed system dependencies (e.g., tailscale CLI).
"""

from __future__ import annotations

from services import network_info


def test_get_tailscale_status_handles_oserror_without_nameerror(
    monkeypatch,
) -> None:
    """Should return a non-running status when the tailscale CLI call errors."""

    monkeypatch.setattr(network_info.shutil, "which", lambda _: "/usr/bin/tailscale")

    def raise_oserror(*_args, **_kwargs):
        raise OSError("boom")

    monkeypatch.setattr(network_info.subprocess, "run", raise_oserror)

    status = network_info.get_tailscale_status()

    assert status.installed is True
    assert status.running is False

