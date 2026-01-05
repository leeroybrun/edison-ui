"""Publisher for realtime updates (T051).

Defines abstract Publisher interface and MemoryPublisher for testing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque

from services.realtime.differ import DiffResult


class Publisher(ABC):
    """Abstract base class for event publishers.

    Publishers receive DiffResults and distribute them to subscribers.
    """

    @abstractmethod
    async def publish(self, result: DiffResult) -> None:
        """Publish a diff result to subscribers.

        Args:
            result: The diff result to publish.
        """
        ...


class MemoryPublisher(Publisher):
    """In-memory publisher for testing.

    Stores events in a deque with max size limit.
    """

    def __init__(self, max_queue_size: int = 1000) -> None:
        """Initialize the memory publisher.

        Args:
            max_queue_size: Maximum number of events to keep.
        """
        self._max_queue_size = max_queue_size
        self._events: deque[DiffResult] = deque(maxlen=max_queue_size)

    async def publish(self, result: DiffResult) -> None:
        """Publish a diff result to the internal queue.

        Args:
            result: The diff result to publish.
        """
        self._events.append(result)

    def get_events(self) -> list[DiffResult]:
        """Get all stored events.

        Returns:
            List of stored DiffResult events.
        """
        return list(self._events)

    def clear(self) -> None:
        """Clear all stored events."""
        self._events.clear()
