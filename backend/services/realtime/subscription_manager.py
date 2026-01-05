"""Subscription manager for WebSocket subscriptions (T050).

Tracks active subscriptions and manages revision numbers per subscription.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Subscription:
    """A subscription to a resource."""

    subscription_id: str
    resource: str
    params: dict[str, Any]
    revision: int = 0


class SubscriptionManager:
    """Manages WebSocket subscriptions and revision tracking."""

    def __init__(self) -> None:
        """Initialize subscription manager."""
        self._subscriptions: dict[str, Subscription] = {}
        self._global_revision: int = 0

    @property
    def subscription_count(self) -> int:
        """Get the number of active subscriptions."""
        return len(self._subscriptions)

    def add_subscription(
        self, subscription_id: str, resource: str, params: dict[str, Any]
    ) -> Subscription:
        """Add a subscription.

        Args:
            subscription_id: Unique subscription identifier.
            resource: Resource type (tasks, sessions, qa, projects).
            params: Subscription parameters (e.g., projectId).

        Returns:
            The created subscription.
        """
        subscription = Subscription(
            subscription_id=subscription_id,
            resource=resource,
            params=params,
            revision=0,
        )
        self._subscriptions[subscription_id] = subscription
        return subscription

    def remove_subscription(self, subscription_id: str) -> bool:
        """Remove a subscription.

        Args:
            subscription_id: The subscription ID to remove.

        Returns:
            True if the subscription was removed, False if not found.
        """
        if subscription_id in self._subscriptions:
            del self._subscriptions[subscription_id]
            return True
        return False

    def has_subscription(self, subscription_id: str) -> bool:
        """Check if a subscription exists.

        Args:
            subscription_id: The subscription ID to check.

        Returns:
            True if the subscription exists.
        """
        return subscription_id in self._subscriptions

    def get_subscription(self, subscription_id: str) -> Subscription | None:
        """Get a subscription by ID.

        Args:
            subscription_id: The subscription ID.

        Returns:
            The subscription or None if not found.
        """
        return self._subscriptions.get(subscription_id)

    def get_next_revision(self, subscription_id: str | None = None) -> int:
        """Get the next revision number.

        Each call returns a monotonically increasing number.

        Args:
            subscription_id: Optional subscription ID (for per-subscription tracking).

        Returns:
            The next revision number.
        """
        self._global_revision += 1
        if subscription_id and subscription_id in self._subscriptions:
            self._subscriptions[subscription_id].revision = self._global_revision
        return self._global_revision
