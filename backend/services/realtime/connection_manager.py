"""Connection manager for WebSocket connections (T050).

Tracks active WebSocket connections across the application.
"""

from __future__ import annotations

from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self) -> None:
        """Initialize connection manager."""
        self._connections: set[WebSocket] = set()

    @property
    def active_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self._connections)

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a WebSocket connection.

        Args:
            websocket: The WebSocket to connect.
        """
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection.

        Args:
            websocket: The WebSocket to disconnect.
        """
        self._connections.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        """Broadcast a message to all connected clients.

        Args:
            message: The message to broadcast.
        """
        for connection in self._connections.copy():
            try:
                await connection.send_json(message)
            except Exception:
                self._connections.discard(connection)
