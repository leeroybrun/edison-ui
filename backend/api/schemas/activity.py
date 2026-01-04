"""Activity API schemas (T044).

Schemas for activity and audit endpoints.
"""
from __future__ import annotations

from pydantic import BaseModel


class Actor(BaseModel):
    """Actor information for activity events."""

    osUser: str
    displayName: str


class ActivityItem(BaseModel):
    """Activity item returned from GET /projects/{projectId}/activity."""

    timestamp: str
    eventType: str
    summary: str
    sessionId: str | None = None
    taskId: str | None = None
    invocationId: str | None = None
    actor: Actor


class ActivityResponse(BaseModel):
    """Response for GET /projects/{projectId}/activity."""

    items: list[ActivityItem]
    hasMore: bool


class AuditEvent(BaseModel):
    """Audit event returned from GET /projects/{projectId}/audit."""

    ts: str
    event: str
    invocationId: str
    sessionId: str | None = None
    command: str
    exitCode: int
    durationMs: int


class AuditResponse(BaseModel):
    """Response for GET /projects/{projectId}/audit."""

    items: list[AuditEvent]
    hasMore: bool
