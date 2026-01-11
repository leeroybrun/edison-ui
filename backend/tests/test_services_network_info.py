"""Tests for network info helpers.

These utilities are used for pairing URL generation and must gracefully handle
missing/failed system dependencies (e.g., tailscale CLI).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from services import network_info


def _write_executable_tailscale_stub(path: Path, *, hostname: str) -> None:
    path.write_text(
        "\n".join(
            [
                "#!/bin/sh",
                'if [ "$1" = "status" ] && [ "$2" = "--json" ]; then',
                "  echo '{\"BackendState\":\"Running\",\"Self\":{\"DNSName\":\""
                + hostname
                + ".\",\"TailscaleIPs\":[\"100.64.0.1\"]}}'",
                "  exit 0",
                "fi",
                "exit 1",
                "",
            ]
        )
    )
    path.chmod(0o755)


def test_get_tailscale_status_uses_configured_cli_candidates_when_not_on_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """If tailscale isn't on PATH, we should still detect it via configured candidates."""
    empty_path_dir = tmp_path / "empty-path"
    empty_path_dir.mkdir()
    monkeypatch.setenv("PATH", str(empty_path_dir))

    candidate = tmp_path / "tailscale-stub"
    _write_executable_tailscale_stub(candidate, hostname="host.tailnet.ts.net")
    monkeypatch.setenv("TAILSCALE_CLI_CANDIDATES", str(candidate))

    status = network_info.get_tailscale_status()

    assert status.installed is True
    assert status.running is True
    assert status.hostname == "host.tailnet.ts.net"
    assert status.ip == "100.64.0.1"


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
