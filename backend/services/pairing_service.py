"""Pairing service for remote mobile access (T061).

Manages pairing codes, token issuance, and validation.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import secrets
import string
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import qrcode


@dataclass
class PairingSession:
    """Represents an active pairing request."""

    pairing_id: str
    display_code: str
    created_at: datetime
    expires_at: datetime
    completed: bool = False
    revoked: bool = False


@dataclass
class PairedDevice:
    """Represents a paired device with a valid token."""

    pairing_id: str
    token_hash: str
    created_at: datetime
    expires_at: datetime
    last_used: datetime | None = None
    revoked: bool = False


@dataclass
class PairingData:
    """Persisted pairing data."""

    sessions: dict[str, PairingSession] = field(default_factory=dict)
    devices: dict[str, PairedDevice] = field(default_factory=dict)


class PairingService:
    """Service for managing device pairing and token validation."""

    # Default expiration times
    PAIRING_CODE_EXPIRY_MINUTES = 5
    TOKEN_EXPIRY_HOURS = 24

    # Display code configuration
    CODE_LENGTH = 6
    CODE_CHARS = string.ascii_uppercase + string.digits

    def __init__(self, storage_path: str | None = None) -> None:
        """Initialize the pairing service.

        Args:
            storage_path: Path to the pairing data file.
                         Defaults to ~/.edison-ui/pairing.json
        """
        if storage_path:
            self.storage_path = Path(storage_path).expanduser().resolve()
        else:
            self.storage_path = (
                Path("~/.edison-ui/pairing.json").expanduser().resolve()
            )

        self._data: PairingData | None = None

    def _load(self) -> PairingData:
        """Load pairing data from file."""
        if self._data is not None:
            return self._data

        if self.storage_path.exists():
            try:
                with open(self.storage_path) as f:
                    raw = json.load(f)

                    sessions = {}
                    for sid, sdata in raw.get("sessions", {}).items():
                        sessions[sid] = PairingSession(
                            pairing_id=sdata["pairing_id"],
                            display_code=sdata["display_code"],
                            created_at=datetime.fromisoformat(sdata["created_at"]),
                            expires_at=datetime.fromisoformat(sdata["expires_at"]),
                            completed=sdata.get("completed", False),
                            revoked=sdata.get("revoked", False),
                        )

                    devices = {}
                    for token_hash, ddata in raw.get("devices", {}).items():
                        devices[token_hash] = PairedDevice(
                            pairing_id=ddata["pairing_id"],
                            token_hash=ddata["token_hash"],
                            created_at=datetime.fromisoformat(ddata["created_at"]),
                            expires_at=datetime.fromisoformat(ddata["expires_at"]),
                            last_used=datetime.fromisoformat(ddata["last_used"])
                            if ddata.get("last_used")
                            else None,
                            revoked=ddata.get("revoked", False),
                        )

                    self._data = PairingData(sessions=sessions, devices=devices)
            except (json.JSONDecodeError, OSError, KeyError):
                self._data = PairingData()
        else:
            self._data = PairingData()

        return self._data

    def _save(self) -> None:
        """Save pairing data to file."""
        if self._data is None:
            return

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        raw: dict[str, Any] = {"sessions": {}, "devices": {}}

        for sid, session in self._data.sessions.items():
            raw["sessions"][sid] = {
                "pairing_id": session.pairing_id,
                "display_code": session.display_code,
                "created_at": session.created_at.isoformat(),
                "expires_at": session.expires_at.isoformat(),
                "completed": session.completed,
                "revoked": session.revoked,
            }

        for token_hash, device in self._data.devices.items():
            raw["devices"][token_hash] = {
                "pairing_id": device.pairing_id,
                "token_hash": device.token_hash,
                "created_at": device.created_at.isoformat(),
                "expires_at": device.expires_at.isoformat(),
                "last_used": device.last_used.isoformat() if device.last_used else None,
                "revoked": device.revoked,
            }

        with open(self.storage_path, "w") as f:
            json.dump(raw, f, indent=2)

    def _generate_display_code(self) -> str:
        """Generate a human-readable display code."""
        return "".join(
            secrets.choice(self.CODE_CHARS) for _ in range(self.CODE_LENGTH)
        )

    def _generate_token(self) -> str:
        """Generate a secure token."""
        return secrets.token_urlsafe(32)

    def _hash_token(self, token: str) -> str:
        """Hash a token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    def _generate_qr_code(self, data: str) -> str:
        """Generate a QR code data URL for the pairing data."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        b64 = base64.b64encode(buffer.read()).decode()
        return f"data:image/png;base64,{b64}"

    def start_pairing(self, base_url: str = "http://localhost:3000") -> dict[str, str]:
        """Start a new pairing session.

        Args:
            base_url: Base URL for the pairing QR code.

        Returns:
            Dictionary with pairingId, displayCode, expiresAt, qrCodeDataUrl.
        """
        data = self._load()

        pairing_id = secrets.token_urlsafe(16)
        display_code = self._generate_display_code()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self.PAIRING_CODE_EXPIRY_MINUTES)

        session = PairingSession(
            pairing_id=pairing_id,
            display_code=display_code,
            created_at=now,
            expires_at=expires_at,
        )

        data.sessions[pairing_id] = session
        self._save()

        # Generate QR code with pairing URL
        pairing_url = f"{base_url}/pair?code={display_code}"
        qr_data_url = self._generate_qr_code(pairing_url)

        return {
            "pairingId": pairing_id,
            "displayCode": display_code,
            "expiresAt": expires_at.isoformat().replace("+00:00", "Z"),
            "qrCodeDataUrl": qr_data_url,
        }

    def complete_pairing(self, display_code: str) -> dict[str, str]:
        """Complete a pairing using the display code.

        Args:
            display_code: The display code from start_pairing.

        Returns:
            Dictionary with token and expiresAt.

        Raises:
            ValueError: If the code is invalid, expired, or already used.
        """
        data = self._load()
        now = datetime.now(timezone.utc)

        # Find the session by display code
        session = None
        for s in data.sessions.values():
            if s.display_code.upper() == display_code.upper():
                session = s
                break

        if session is None:
            raise ValueError("Invalid pairing code")

        if session.revoked:
            raise ValueError("Pairing code has been revoked")

        if session.completed:
            raise ValueError("Pairing code has already been used")

        if now > session.expires_at:
            raise ValueError("Pairing code has expired")

        # Mark session as completed
        session.completed = True

        # Generate token
        token = self._generate_token()
        token_hash = self._hash_token(token)
        token_expires = now + timedelta(hours=self.TOKEN_EXPIRY_HOURS)

        # Create paired device
        device = PairedDevice(
            pairing_id=session.pairing_id,
            token_hash=token_hash,
            created_at=now,
            expires_at=token_expires,
        )
        data.devices[token_hash] = device

        self._save()

        return {
            "token": token,
            "expiresAt": token_expires.isoformat().replace("+00:00", "Z"),
        }

    def validate_token(self, token: str) -> bool:
        """Validate a bearer token.

        Args:
            token: The bearer token to validate.

        Returns:
            True if the token is valid, False otherwise.
        """
        data = self._load()
        token_hash = self._hash_token(token)
        now = datetime.now(timezone.utc)

        device = data.devices.get(token_hash)
        if device is None:
            return False

        if device.revoked:
            return False

        if now > device.expires_at:
            return False

        # Update last_used
        device.last_used = now
        self._save()

        return True

    def revoke_pairing(self, pairing_id: str) -> bool:
        """Revoke a pairing session.

        Args:
            pairing_id: The pairing ID to revoke.

        Returns:
            True if found and revoked, False if not found.
        """
        data = self._load()

        session = data.sessions.get(pairing_id)
        if session is None:
            return False

        session.revoked = True

        # Also revoke any associated tokens
        for device in data.devices.values():
            if device.pairing_id == pairing_id:
                device.revoked = True

        self._save()
        return True

    def revoke_token(self, token: str) -> bool:
        """Revoke a specific token.

        Args:
            token: The token to revoke.

        Returns:
            True if found and revoked, False if not found.
        """
        data = self._load()
        token_hash = self._hash_token(token)

        device = data.devices.get(token_hash)
        if device is None:
            return False

        device.revoked = True
        self._save()
        return True

    def get_pairing_status(self, pairing_id: str) -> dict[str, Any] | None:
        """Get the status of a pairing session.

        Args:
            pairing_id: The pairing session ID.

        Returns:
            Dictionary with status info, or None if not found.
            - status: "pending" | "completed" | "expired" | "revoked"
            - expiresAt: ISO timestamp when code expires
            - completed: Whether pairing was completed
        """
        data = self._load()
        now = datetime.now(timezone.utc)

        session = data.sessions.get(pairing_id)
        if session is None:
            return None

        # Determine status
        if session.revoked:
            status = "revoked"
        elif session.completed:
            status = "completed"
        elif now > session.expires_at:
            status = "expired"
        else:
            status = "pending"

        return {
            "pairingId": session.pairing_id,
            "status": status,
            "expiresAt": session.expires_at.isoformat().replace("+00:00", "Z"),
            "completed": session.completed,
        }

    def list_pairings(self) -> list[dict[str, Any]]:
        """List all active paired devices.

        Returns:
            List of pairing info dictionaries.
        """
        data = self._load()
        now = datetime.now(timezone.utc)
        result = []

        for device in data.devices.values():
            if device.revoked or now > device.expires_at:
                continue

            result.append({
                "pairingId": device.pairing_id,
                "createdAt": device.created_at.isoformat().replace("+00:00", "Z"),
                "expiresAt": device.expires_at.isoformat().replace("+00:00", "Z"),
                "lastUsed": device.last_used.isoformat().replace("+00:00", "Z")
                if device.last_used
                else None,
            })

        return result

    def _expire_all_pairings(self) -> None:
        """Test helper to expire all active pairing sessions."""
        data = self._load()
        expired = datetime.now(timezone.utc) - timedelta(hours=1)

        for session in data.sessions.values():
            session.expires_at = expired

        self._save()


# Singleton instance management
_pairing_service: PairingService | None = None


def get_pairing_service() -> PairingService:
    """Get the pairing service singleton."""
    global _pairing_service
    if _pairing_service is None:
        storage_path = os.environ.get("PAIRING_FILE")
        _pairing_service = PairingService(storage_path=storage_path)
    return _pairing_service


def reset_pairing_service() -> None:
    """Reset the pairing service singleton (for testing)."""
    global _pairing_service
    _pairing_service = None
