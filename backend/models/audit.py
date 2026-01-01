"""Audit entry models for tracking actions.

AuditEntry captures who did what, when, to what entity, and the outcome.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from models.actor import ActorIdentity


class AuditTarget(BaseModel):
    """Target entity of an audit action.

    Attributes:
        entity_type: Type of entity (e.g., "task", "session", "qa").
        entity_id: Unique identifier of the entity.
    """

    entity_type: str
    entity_id: str


class AuditEntry(BaseModel):
    """A single audit log entry.

    Attributes:
        action_id: Unique identifier for this action.
        actor: Who performed the action.
        timestamp: When the action occurred (UTC).
        action_type: Type of action performed.
        target: Entity the action was performed on.
        outcome: Result of the action (success/failure/blocked).
        context: Additional context (must NOT contain secrets).
    """

    action_id: str
    actor: ActorIdentity
    timestamp: datetime
    action_type: str
    target: AuditTarget
    outcome: str
    context: dict[str, Any] | None = None
