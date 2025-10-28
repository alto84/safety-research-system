"""
Event Bus (Pub/Sub)

Simple pub/sub event bus for broadcasting events to multiple subscribers.
Decouples event producers from consumers.
"""

from collections import defaultdict
from typing import Callable, Any, List, Dict
import threading
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """
    Simple pub/sub event bus for broadcasting events to multiple subscribers.

    Use cases:
    - Audit events (log to multiple destinations)
    - Status updates (notify dashboard, logger, metrics)
    - Alerts (notify human, log, escalate)
    - Performance metrics (track message flow)

    Features:
    - Multiple subscribers per event type
    - Wildcard subscriptions ("*" for all events)
    - Thread-safe operations
    - Exception isolation (one subscriber failure doesn't affect others)

    Example:
        >>> bus = EventBus()
        >>>
        >>> # Subscribe to specific event
        >>> def on_task_complete(data):
        ...     print(f"Task {data['task_id']} completed")
        >>>
        >>> bus.subscribe("task.completed", on_task_complete)
        >>>
        >>> # Subscribe to all events
        >>> bus.subscribe("*", lambda data: print(f"Event: {data}"))
        >>>
        >>> # Publish event
        >>> bus.publish("task.completed", {"task_id": "task-123"})
    """

    def __init__(self):
        # Event type -> list of callbacks
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.lock = threading.Lock()

        # Statistics
        self.stats_lock = threading.Lock()
        self.total_published = 0
        self.total_callbacks_executed = 0
        self.total_callback_errors = 0

    def subscribe(self, event_type: str, callback: Callable[[Any], None]):
        """
        Subscribe to event type.

        Args:
            event_type: Event to subscribe to (e.g., "task.completed")
                       Use "*" to subscribe to all events
            callback: Function to call when event published.
                     Should accept one argument (event data).

        Example:
            >>> def log_event(data):
            ...     print(f"Event received: {data}")
            >>>
            >>> bus.subscribe("message.sent", log_event)
        """
        with self.lock:
            self.subscribers[event_type].append(callback)

        logger.debug(f"Subscribed to '{event_type}' ({len(self.subscribers[event_type])} subscribers)")

    def unsubscribe(self, event_type: str, callback: Callable):
        """
        Remove subscription.

        Args:
            event_type: Event type to unsubscribe from
            callback: Callback function to remove
        """
        with self.lock:
            if callback in self.subscribers[event_type]:
                self.subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from '{event_type}'")

    def publish(self, event_type: str, data: Any):
        """
        Publish event to all subscribers.

        Executes callbacks synchronously but isolates exceptions.
        One failing callback doesn't prevent others from running.

        Args:
            event_type: Type of event (e.g., "task.completed")
            data: Event data (any type - typically dict)

        Example:
            >>> bus.publish("task.completed", {
            ...     "task_id": "task-123",
            ...     "status": "success",
            ...     "duration_ms": 1523
            ... })
        """
        # Get subscribers (copy to avoid deadlock during callback execution)
        with self.lock:
            # Specific subscribers + wildcard subscribers
            specific_callbacks = self.subscribers[event_type].copy()
            wildcard_callbacks = self.subscribers.get("*", []).copy()

        all_callbacks = specific_callbacks + wildcard_callbacks

        # Update stats
        with self.stats_lock:
            self.total_published += 1

        # Execute callbacks outside lock (avoid deadlock if callback publishes)
        for callback in all_callbacks:
            try:
                callback(data)

                with self.stats_lock:
                    self.total_callbacks_executed += 1

            except Exception as e:
                # Log error but continue to other callbacks
                logger.error(
                    f"EventBus callback error for '{event_type}': {e}",
                    exc_info=True
                )

                with self.stats_lock:
                    self.total_callback_errors += 1

        if all_callbacks:
            logger.debug(
                f"Published '{event_type}' to {len(all_callbacks)} subscribers "
                f"({len(specific_callbacks)} specific, {len(wildcard_callbacks)} wildcard)"
            )

    def publish_async(self, event_type: str, data: Any):
        """
        Publish event asynchronously in a background thread.

        Use when you don't want to block on callback execution.

        Args:
            event_type: Type of event
            data: Event data
        """
        thread = threading.Thread(
            target=self.publish,
            args=(event_type, data),
            daemon=True
        )
        thread.start()

    def get_subscriber_count(self, event_type: str) -> int:
        """
        Get number of subscribers for event type.

        Args:
            event_type: Event type to check

        Returns:
            Number of subscribers
        """
        with self.lock:
            return len(self.subscribers.get(event_type, []))

    def get_all_event_types(self) -> List[str]:
        """
        Get list of all event types with subscribers.

        Returns:
            List of event type strings
        """
        with self.lock:
            return list(self.subscribers.keys())

    def get_stats(self) -> Dict[str, Any]:
        """
        Get event bus statistics.

        Returns:
            Dictionary with stats
        """
        with self.stats_lock:
            stats = {
                "total_published": self.total_published,
                "total_callbacks_executed": self.total_callbacks_executed,
                "total_callback_errors": self.total_callback_errors,
                "event_types": {}
            }

        with self.lock:
            for event_type, callbacks in self.subscribers.items():
                stats["event_types"][event_type] = len(callbacks)

        return stats

    def clear(self):
        """
        Remove all subscriptions.

        WARNING: All subscribers will be removed.
        """
        with self.lock:
            self.subscribers.clear()

        logger.warning("Cleared all event bus subscriptions")
