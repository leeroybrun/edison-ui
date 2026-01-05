"""Guard response schemas for API endpoints.

Provides schemas for guard checks, previews, and action results.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class GuardCheckResult(BaseModel):
    """Result of a single guard check.

    Attributes:
        allowed: Whether the guard allows the action.
        guard_name: Name of the guard that was checked.
        reason: Explanation if blocked (None if allowed).
        required_state: The state required by this guard (None if not applicable).
        current_state: The current state that was checked (None if not applicable).
    """

    allowed: bool
    guard_name: str
    reason: str | None = None
    required_state: str | None = None
    current_state: str | None = None


class GuardPreviewResponse(BaseModel):
    """Response for guard preview (dry-run) requests.

    Attributes:
        can_proceed: Whether all guards allow the action.
        checks: List of individual guard check results.
        warnings: Non-blocking warnings (empty list by default).
    """

    can_proceed: bool
    checks: list[GuardCheckResult]
    warnings: list[str] = []


class GuardApplyResponse(BaseModel):
    """Response for guard-protected action execution.

    Attributes:
        success: Whether the action completed successfully.
        result: The result data from the action (None if failed).
        audit_entry_id: ID of the audit log entry for this action.
    """

    success: bool
    result: dict[str, Any] | None = None
    audit_entry_id: str | None = None
