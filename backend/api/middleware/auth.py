"""Authentication middleware for network-exposed mode (T060).

When exposure_mode is "network", all sensitive endpoints require
Bearer token authentication from a paired device.
"""

from __future__ import annotations

import os
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from services.pairing_service import get_pairing_service, reset_pairing_service
from services.settings_manager import SettingsManager

# Paths that don't require authentication even in network mode
AUTH_EXEMPT_PATHS = {
    "/api/v1/health",
    "/api/v1/pairing/start",
    "/api/v1/pairing/complete",
    "/api/v1/settings",  # Settings read access needed for UI bootstrap
    "/api/v1/settings/exposure-mode",
    # WebSocket is handled separately
    "/api/v1/ws/realtime",
}

# Path prefixes that are exempt (for dynamic paths like /pairing/{id})
AUTH_EXEMPT_PATH_PREFIXES_DYNAMIC = [
    "/api/v1/pairing/",  # Allow access to pairing endpoints for revoke
]

# Path prefixes that don't require auth
AUTH_EXEMPT_PREFIXES = [
    "/docs",
    "/openapi.json",
    "/redoc",
]


def get_settings_manager() -> SettingsManager:
    """Get a configured settings manager."""
    settings_file = os.environ.get("SETTINGS_FILE")
    return SettingsManager(settings_file=settings_file)


def is_path_exempt(path: str) -> bool:
    """Check if a path is exempt from authentication."""
    if path in AUTH_EXEMPT_PATHS:
        return True

    for prefix in AUTH_EXEMPT_PREFIXES:
        if path.startswith(prefix):
            return True

    for prefix in AUTH_EXEMPT_PATH_PREFIXES_DYNAMIC:
        if path.startswith(prefix):
            return True

    return False


def extract_bearer_token(authorization: str | None) -> str | None:
    """Extract bearer token from Authorization header.

    Args:
        authorization: The Authorization header value.

    Returns:
        The token if valid Bearer format, None otherwise.
    """
    if not authorization:
        return None

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce authentication in network-exposed mode."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process the request and enforce auth if needed."""
        path = request.url.path

        # Check if path is exempt
        if is_path_exempt(path):
            return await call_next(request)

        # Check exposure mode
        manager = get_settings_manager()
        settings = manager.get_settings()

        # In localhost mode, no auth required
        if settings.exposure_mode == "localhost":
            return await call_next(request)

        # In network mode, require auth
        authorization = request.headers.get("authorization")
        token = extract_bearer_token(authorization)

        if token is None:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Authorization required. Please pair your device first."
                },
            )

        # Reset singleton to ensure fresh load for tests
        reset_pairing_service()
        pairing_service = get_pairing_service()

        if not pairing_service.validate_token(token):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token."},
            )

        # Store token in request state for use in endpoints
        request.state.token = token

        return await call_next(request)


def get_current_token(request: Request) -> str | None:
    """Get the current authenticated token from the request.

    Args:
        request: The FastAPI request.

    Returns:
        The token if authenticated, None otherwise.
    """
    return getattr(request.state, "token", None)
