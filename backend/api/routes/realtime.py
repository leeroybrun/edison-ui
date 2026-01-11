"""WebSocket realtime endpoint (T050, T063).

Implements push-first realtime updates per FR-006 and data-model.md contracts.

Protocol:
- Client sends: {"type": "subscribe", "subscriptionId": "...", "resource": "...", "params": {...}}
- Client sends: {"type": "unsubscribe", "subscriptionId": "..."}
- Server sends: {"type": "snapshot", "subscriptionId": "...", "revision": N, "data": [...]}
- Server sends: {"type": "upsert", "subscriptionId": "...", "revision": N, "data": {...}}
- Server sends: {"type": "delete", "subscriptionId": "...", "revision": N, "id": "..."}
- Server sends: {"type": "error", "subscriptionId": "...", "code": "...", "message": "..."}

Authentication (T063):
- In localhost mode: No auth required
- In network mode: Pass token via ?token= query param or Sec-WebSocket-Protocol header
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from core.settings import get_settings
from services.pairing_service import get_pairing_service, reset_pairing_service
from services.project_discovery import ProjectDiscoveryService
from services.qa_reader import QAReaderService
from services.session_reader import SessionReaderService
from services.settings_manager import SettingsManager
from services.task_reader import TaskReaderService

router = APIRouter(prefix="/ws", tags=["realtime"])


def get_settings_manager() -> SettingsManager:
    """Get a configured settings manager."""
    settings_file = os.environ.get("SETTINGS_FILE")
    return SettingsManager(settings_file=settings_file)


def extract_websocket_token(
    websocket: WebSocket, token_param: str | None
) -> str | None:
    """Extract authentication token from WebSocket connection.

    Checks in order:
    1. Query parameter ?token=
    2. Sec-WebSocket-Protocol header (format: "bearer.{token}")

    Args:
        websocket: The WebSocket connection.
        token_param: Token from query parameter.

    Returns:
        The token if found, None otherwise.
    """
    # Check query param first
    if token_param:
        return token_param

    # Check Sec-WebSocket-Protocol header
    # Format: "bearer.{token}"
    subprotocols: list[str] = websocket.scope.get("subprotocols", [])
    for protocol in subprotocols:
        if protocol.startswith("bearer."):
            return str(protocol[7:])  # Remove "bearer." prefix

    return None


async def check_websocket_auth(
    websocket: WebSocket, token_param: str | None
) -> tuple[bool, str | None]:
    """Check if WebSocket connection is authenticated.

    Args:
        websocket: The WebSocket connection.
        token_param: Token from query parameter.

    Returns:
        Tuple of (is_authenticated, error_message).
        In localhost mode, always returns (True, None).
    """
    # Get exposure mode
    manager = get_settings_manager()
    settings = manager.get_settings()

    # In localhost mode, no auth required
    if settings.exposure_mode == "localhost":
        return True, None

    # In network mode, require auth
    token = extract_websocket_token(websocket, token_param)

    if token is None:
        return False, "Authorization required. Please pair your device first."

    # Validate token
    reset_pairing_service()
    pairing_service = get_pairing_service()

    if not pairing_service.validate_token(token):
        return False, "Invalid or expired token."

    return True, None


# Valid resource types
VALID_RESOURCES = {"tasks", "sessions", "qa", "projects"}

# Resources that require projectId param
PROJECT_SCOPED_RESOURCES = {"tasks", "sessions", "qa"}


def get_discovery_service() -> ProjectDiscoveryService:
    """Get a configured project discovery service."""
    settings = get_settings()
    return ProjectDiscoveryService(
        scan_roots=settings.get_expanded_scan_roots(),
        ignore_patterns=settings.scan_ignore_patterns,
        pin_storage_path=settings.get_expanded_pin_storage_path(),
    )


def get_project_path(project_id: str) -> str | None:
    """Get the project path from project ID.

    Returns:
        The project path, or None if not found.
    """
    service = get_discovery_service()
    project = service.get_project_by_id(project_id)
    if project is None:
        return None
    return project.path


class ConnectionManager:
    """Manages WebSocket connections and subscriptions."""

    def __init__(self) -> None:
        self.subscriptions: dict[str, dict[str, Any]] = {}
        self.revision_counter: int = 0

    def get_next_revision(self) -> int:
        """Get the next revision number."""
        self.revision_counter += 1
        return self.revision_counter

    def add_subscription(
        self, subscription_id: str, resource: str, params: dict[str, Any]
    ) -> None:
        """Add a subscription."""
        self.subscriptions[subscription_id] = {
            "resource": resource,
            "params": params,
        }

    def remove_subscription(self, subscription_id: str) -> bool:
        """Remove a subscription. Returns True if found."""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            return True
        return False

    def has_subscription(self, subscription_id: str) -> bool:
        """Check if subscription exists."""
        return subscription_id in self.subscriptions


def build_error_response(
    code: str, message: str, subscription_id: str | None = None
) -> dict[str, Any]:
    """Build an error response."""
    response: dict[str, Any] = {
        "type": "error",
        "code": code,
        "message": message,
    }
    if subscription_id:
        response["subscriptionId"] = subscription_id
    return response


def get_tasks_snapshot(
    project_path: str,
    state_filter: str | None = None,
    session_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Get task data for snapshot.

    Args:
        project_path: Path to the project.
        state_filter: Optional filter by task state.
        session_filter: Optional filter by session ID.

    Returns:
        List of task data dicts.
    """
    reader = TaskReaderService(project_path)

    # Apply filters via list_tasks
    states = [state_filter] if state_filter else None
    tasks = reader.list_tasks(session_id=session_filter, states=states)

    # Convert to API format
    result = []
    for task in tasks:
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "taskId": task.task_id,
            "title": task.title,
            "state": task.state,
            "sessionId": task.session_id,
            "parentId": task.parent_id,
            "childIds": task.child_ids or [],
            "dependsOn": task.depends_on or [],
            "blocksTasks": task.blocks_tasks or [],
            "validationStatus": "unknown",
            "validation": {
                "status": "unknown",
                "lastRound": None,
                "validatorCount": 0,
                "lastUpdated": now,
            },
            "latestVerdict": None,
            "ready": True,  # Simplified for now
            "blockedBy": [],
            "createdAt": task.created_at or now,
            "updatedAt": task.updated_at or now,
        }
        result.append(item)
    return result


def get_sessions_snapshot(project_path: str) -> list[dict[str, Any]]:
    """Get session data for snapshot."""
    reader = SessionReaderService(project_path)
    sessions = reader.list_sessions()

    result = []
    for session in sessions:
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "sessionId": session.session_id,
            "state": session.state,
            "phase": session.phase,
            "createdAt": session.created_at or now,
            "lastActive": session.last_active_at or now,
            "worktreePath": None,  # Not in basic Session dataclass
            "branchName": session.git.branch_name if session.git else None,
        }
        result.append(item)
    return result


def get_qa_snapshot(project_path: str) -> list[dict[str, Any]]:
    """Get QA data for snapshot."""
    reader = QAReaderService(project_path)
    records = reader._load_all_qa()

    result = []
    for record in records:
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "qaId": record.qa_id,
            "taskId": record.task_id,
            "title": f"QA for {record.task_id}",
            "state": record.state,
            "round": record.round,
            "sessionId": record.session_id,
            "createdAt": record.created_at or now,
            "updatedAt": record.updated_at or now,
        }
        result.append(item)
    return result


def get_projects_snapshot() -> list[dict[str, Any]]:
    """Get projects data for snapshot."""
    service = get_discovery_service()
    projects = service.discover_projects()

    result = []
    for project in projects:
        item = {
            "projectId": project.project_id,
            "name": project.name,
            "pinned": project.pinned,
            "hasGit": project.has_git,
            "health": {
                "tasks": project.health.task_count,
                "sessions": project.health.session_count,
                "qa": project.health.qa_count,
            }
            if project.health
            else {"tasks": 0, "sessions": 0, "qa": 0},
        }
        result.append(item)
    return result


@router.websocket("/realtime")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    """WebSocket endpoint for realtime updates.

    In network-exposed mode, authentication is required via:
    - Query parameter: ?token={bearer_token}
    - Subprotocol header: bearer.{token}
    """
    # Check authentication before accepting connection
    is_authenticated, error_message = await check_websocket_auth(websocket, token)

    if not is_authenticated:
        # Accept connection briefly to send error, then close
        await websocket.accept()
        await websocket.send_json(
            build_error_response(
                code="AUTH_REQUIRED",
                message=error_message or "Authentication required",
            )
        )
        await websocket.close(code=4001)  # 4001 = Unauthorized
        return

    # Accept the connection (with subprotocol if used)
    subprotocols = websocket.scope.get("subprotocols", [])
    accepted_subprotocol = None
    for protocol in subprotocols:
        if protocol.startswith("bearer."):
            accepted_subprotocol = protocol
            break

    if accepted_subprotocol:
        await websocket.accept(subprotocol=accepted_subprotocol)
    else:
        await websocket.accept()

    manager = ConnectionManager()

    try:
        while True:
            # Receive message
            try:
                data = await websocket.receive_text()
            except WebSocketDisconnect:
                break

            # Parse JSON
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json(
                    build_error_response(
                        code="INVALID_JSON",
                        message="Failed to parse JSON",
                    )
                )
                continue

            # Validate message has type
            if "type" not in message:
                await websocket.send_json(
                    build_error_response(
                        code="INVALID_MESSAGE",
                        message="Message must have a 'type' field",
                    )
                )
                continue

            msg_type = message.get("type")

            # Handle ping (for connection testing)
            if msg_type == "ping":
                continue  # Just ignore ping messages

            # Handle subscribe
            if msg_type == "subscribe":
                subscription_id = message.get("subscriptionId")
                resource = message.get("resource")
                params = message.get("params", {})

                # Validate subscriptionId
                if not subscription_id:
                    await websocket.send_json(
                        build_error_response(
                            code="INVALID_MESSAGE",
                            message="Subscribe message must have 'subscriptionId'",
                        )
                    )
                    continue

                # Check for duplicate subscription
                if manager.has_subscription(subscription_id):
                    await websocket.send_json(
                        build_error_response(
                            code="DUPLICATE_SUBSCRIPTION",
                            message=f"Subscription already exists: {subscription_id}",
                            subscription_id=subscription_id,
                        )
                    )
                    continue

                # Validate resource
                if not resource:
                    await websocket.send_json(
                        build_error_response(
                            code="INVALID_MESSAGE",
                            message="Subscribe message must have 'resource'",
                            subscription_id=subscription_id,
                        )
                    )
                    continue

                if resource not in VALID_RESOURCES:
                    await websocket.send_json(
                        build_error_response(
                            code="INVALID_RESOURCE",
                            message=f"Invalid resource: {resource}",
                            subscription_id=subscription_id,
                        )
                    )
                    continue

                # Validate projectId for project-scoped resources
                if resource in PROJECT_SCOPED_RESOURCES:
                    project_id = params.get("projectId")
                    if not project_id:
                        await websocket.send_json(
                            build_error_response(
                                code="MISSING_PARAM",
                                message=f"Resource '{resource}' requires 'projectId' param",
                                subscription_id=subscription_id,
                            )
                        )
                        continue

                    project_path = get_project_path(project_id)
                    if project_path is None:
                        await websocket.send_json(
                            build_error_response(
                                code="PROJECT_NOT_FOUND",
                                message=f"Project not found: {project_id}",
                                subscription_id=subscription_id,
                            )
                        )
                        continue

                # Get snapshot data
                try:
                    if resource == "tasks":
                        # Extract optional filters
                        state_filter = params.get("state")
                        session_filter = params.get("sessionId")
                        snapshot_data = get_tasks_snapshot(
                            project_path,  # type: ignore[arg-type]
                            state_filter=state_filter,
                            session_filter=session_filter,
                        )
                    elif resource == "sessions":
                        snapshot_data = get_sessions_snapshot(project_path)  # type: ignore[arg-type]
                    elif resource == "qa":
                        snapshot_data = get_qa_snapshot(project_path)  # type: ignore[arg-type]
                    elif resource == "projects":
                        snapshot_data = get_projects_snapshot()
                    else:
                        snapshot_data = []

                except Exception as e:
                    await websocket.send_json(
                        build_error_response(
                            code="SNAPSHOT_ERROR",
                            message=f"Failed to get snapshot: {e!s}",
                            subscription_id=subscription_id,
                        )
                    )
                    continue

                # Register subscription
                manager.add_subscription(subscription_id, resource, params)

                # Send snapshot
                await websocket.send_json(
                    {
                        "type": "snapshot",
                        "subscriptionId": subscription_id,
                        "revision": manager.get_next_revision(),
                        "data": snapshot_data,
                    }
                )
                continue

            # Handle unsubscribe
            if msg_type == "unsubscribe":
                subscription_id = message.get("subscriptionId")

                if not subscription_id:
                    await websocket.send_json(
                        build_error_response(
                            code="INVALID_MESSAGE",
                            message="Unsubscribe message must have 'subscriptionId'",
                        )
                    )
                    continue

                if not manager.remove_subscription(subscription_id):
                    await websocket.send_json(
                        build_error_response(
                            code="SUBSCRIPTION_NOT_FOUND",
                            message=f"Subscription not found: {subscription_id}",
                            subscription_id=subscription_id,
                        )
                    )
                continue

            # Unknown message type
            await websocket.send_json(
                build_error_response(
                    code="UNKNOWN_MESSAGE_TYPE",
                    message=f"Unknown message type: {msg_type}",
                    subscription_id=message.get("subscriptionId"),
                )
            )

    except WebSocketDisconnect:
        pass  # Normal disconnection
