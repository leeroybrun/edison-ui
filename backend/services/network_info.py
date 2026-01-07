"""Network information service for pairing URL generation.

Provides utilities for detecting local network IPs and Tailscale status.
"""

from __future__ import annotations

import shutil
import socket
import subprocess
from dataclasses import dataclass


@dataclass
class TailscaleStatus:
    """Tailscale status information."""

    installed: bool
    running: bool
    hostname: str | None
    ip: str | None


def get_local_ip() -> str | None:
    """Get the local network IP address.

    Returns:
        The local IP address or None if not available.
    """
    try:
        # Create a socket to determine which interface would be used
        # to reach an external address (doesn't actually connect)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        try:
            # Use Google's DNS as a reference (doesn't actually connect)
            s.connect(("8.8.8.8", 80))
            ip: str = s.getsockname()[0]
            return ip
        finally:
            s.close()
    except (OSError, socket.error):
        return None


def get_tailscale_status() -> TailscaleStatus:
    """Get Tailscale status information.

    Returns:
        TailscaleStatus with installation and connection info.
    """
    # Check if tailscale CLI is installed
    tailscale_path = shutil.which("tailscale")
    if not tailscale_path:
        return TailscaleStatus(installed=False, running=False, hostname=None, ip=None)

    # Try to get tailscale status
    try:
        result = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            # Tailscale installed but not running
            return TailscaleStatus(installed=True, running=False, hostname=None, ip=None)

        import json

        status = json.loads(result.stdout)

        # Check if Tailscale is actually connected
        # BackendState == "Running" and Self is populated
        backend_state = status.get("BackendState", "")
        if backend_state != "Running":
            return TailscaleStatus(installed=True, running=False, hostname=None, ip=None)

        # Get self info
        self_info = status.get("Self", {})
        hostname = self_info.get("DNSName", "").rstrip(".")
        tailscale_ips = self_info.get("TailscaleIPs", [])

        # Get IPv4 address (prefer IPv4 over IPv6)
        ip = None
        for addr in tailscale_ips:
            if "." in addr:  # IPv4
                ip = addr
                break
        if ip is None and tailscale_ips:
            ip = tailscale_ips[0]

        return TailscaleStatus(
            installed=True,
            running=True,
            hostname=hostname if hostname else None,
            ip=ip,
        )

    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return TailscaleStatus(installed=True, running=False, hostname=None, ip=None)


def get_pairing_base_url(exposure_mode: str, frontend_port: int = 3000) -> str:
    """Get the appropriate base URL for pairing based on exposure mode.

    Args:
        exposure_mode: One of 'localhost', 'network', or 'tailscale'.
        frontend_port: The frontend port number.

    Returns:
        The base URL for the pairing QR code.
    """
    if exposure_mode == "localhost":
        return f"http://localhost:{frontend_port}"

    if exposure_mode == "tailscale":
        ts_status = get_tailscale_status()
        if ts_status.running and ts_status.hostname:
            return f"http://{ts_status.hostname}:{frontend_port}"
        # Fallback to network IP if tailscale not available
        local_ip = get_local_ip()
        if local_ip:
            return f"http://{local_ip}:{frontend_port}"
        return f"http://localhost:{frontend_port}"

    if exposure_mode == "network":
        local_ip = get_local_ip()
        if local_ip:
            return f"http://{local_ip}:{frontend_port}"
        # Fallback to localhost if no network IP
        return f"http://localhost:{frontend_port}"

    # Default to localhost for unknown modes
    return f"http://localhost:{frontend_port}"
