"""
Event Bus System - Event-driven architecture for SimpleMem

Implements a pub/sub pattern for decoupling components through async events.
Enables components to emit events without knowing subscribers, and vice versa.

Type: Core Infrastructure
Status: Production Ready
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional, Set, Any
from uuid import uuid4
import logging

# Configure logging
logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events that can be published in the system."""
    
    # Analysis events
    SENTIMENT_ANALYZED = "sentiment_analyzed"
    TEXT_SUMMARIZED = "text_summarized"
    ENTITY_LINKED = "entity_linked"
    DOCUMENTS_CLUSTERED = "documents_clustered"
    
    # Query events
    QUERY_EXECUTED = "query_executed"
    SEARCH_PERFORMED = "search_performed"
    
    # System events
    ERROR_OCCURRED = "error_occurred"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    AUTHENTICATION_FAILED = "authentication_failed"
    REQUEST_RATE_LIMITED = "request_rate_limited"
    
    # Data events
    DATA_STORED = "data_stored"
    DATA_DELETED = "data_deleted"
    DATA_UPDATED = "data_updated"


@dataclass
class Event:
    """Represents a single event in the system.
    
    Attributes:
        type: The type of event (EventType enum)
        source: Module/component that emitted the event
        data: Event-specific data payload
        metadata: Additional metadata (request_id, user_id, etc.)
        timestamp: When the event was created
        id: Unique event identifier
    """
    
    type: EventType
    source: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    id: str = field(default_factory=lambda: str(uuid4()))
    
    def __post_init__(self) -> None:
        """Validate event after initialization."""
        if not self.source:
            raise ValueError("Event source cannot be empty")
        if not isinstance(self.type, EventType):
            raise TypeError("Event type must be an EventType enum")
    
    def matches_filter(self, filter_criteria: Dict[str, Any]) -> bool:
        """Check if event matches filter criteria.
        
        Args:
            filter_criteria: Dictionary of criteria to match
            
        Returns:
            True if event matches all criteria, False otherwise
        """
        for key, value in filter_criteria.items():
            if key == "type":
                if self.type != value:
                    return False
            elif key == "source":
                if isinstance(value, str):
                    if self.source != value:
                        return False
                elif isinstance(value, list):
                    if self.source not in value:
                        return False
            elif key in self.data:
                if self.data[key] != value:
                    return False
            elif key in self.metadata:
                if self.metadata[key] != value:
                    return False
        return True


class EventHandler:
    """Base class for event handlers.
    
    Handlers can be sync or async functions that process events.
    """
    
    def __init__(self, callback: Callable, name: str = ""):
        """Initialize event handler.
        
        Args:
            callback: Function to call when event is triggered
            name: Optional name for the handler
        """
        self.callback = callback
        self.name = name or getattr(callback, "__name__", "handler")
        self.is_async = asyncio.iscoroutinefunction(callback)
    
    async def handle(self, event: Event) -> None:
        """Handle an event.
        
        Args:
            event: Event to handle
        """
        try:
            if self.is_async:
                await self.callback(event)
            else:
                self.callback(event)
        except Exception as e:
            logger.error(f"Error in handler {self.name} processing event {event.type.value}: {e}", 
                        exc_info=True)
    
    def __repr__(self) -> str:
        """String representation of handler."""
        return f"EventHandler(name={self.name}, async={self.is_async})"


class EventBus:
    """Central event bus for pub/sub event system.
    
    Manages event publication and subscription with filtering support.
    Supports both sync and async event handlers.
    
    Attributes:
        _subscribers: Dictionary mapping event types to handler lists
        _event_queue: Queue of pending events to process
        _running: Flag indicating if bus is active
        _stats: Event statistics
    """
    
    def __init__(self):
        """Initialize the event bus."""
        self._subscribers: Dict[EventType, List[EventHandler]] = {}
        self._global_handlers: List[tuple] = []  # (handler, filter_criteria)
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running: bool = False
        self._stats = {
            "published": 0,
            "processed": 0,
            "errors": 0,
        }
        logger.debug("EventBus initialized")
    
    def subscribe(
        self, 
        event_type: EventType, 
        handler: Callable,
        filter_criteria: Optional[Dict[str, Any]] = None,
        name: str = ""
    ) -> None:
        """Subscribe to events of a specific type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Callback function (sync or async)
            filter_criteria: Optional criteria to filter events
            name: Optional name for the handler
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        handler_obj = EventHandler(handler, name or f"handler_{len(self._subscribers[event_type])}")
        
        if filter_criteria:
            self._global_handlers.append((handler_obj, filter_criteria))
        else:
            self._subscribers[event_type].append(handler_obj)
        
        logger.debug(f"Handler {handler_obj.name} subscribed to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, handler: Callable) -> bool:
        """Unsubscribe a handler from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler to remove
            
        Returns:
            True if handler was removed, False if not found
        """
        if event_type not in self._subscribers:
            return False
        
        for i, h in enumerate(self._subscribers[event_type]):
            if h.callback == handler:
                self._subscribers[event_type].pop(i)
                logger.debug(f"Handler unsubscribed from {event_type.value}")
                return True
        return False
    
    def publish(self, event: Event) -> None:
        """Publish an event to the bus.
        
        Args:
            event: Event to publish
        """
        if not isinstance(event, Event):
            raise TypeError("Published object must be an Event instance")
        
        self._stats["published"] += 1
        logger.debug(f"Event published: {event.type.value} from {event.source}")
        
        # Queue event for async processing
        try:
            self._event_queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning(f"Event queue full, dropping event {event.id}")
    
    async def _process_events(self) -> None:
        """Process events from the queue (internal).
        
        This runs in the background when the bus is started.
        """
        while self._running:
            try:
                # Get event with timeout to allow checking _running flag
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=0.1
                )
                
                # Get type-specific handlers
                handlers = self._subscribers.get(event.type, [])
                
                # Get global handlers matching filter criteria
                matching_global = [
                    h for h, criteria in self._global_handlers
                    if event.matches_filter(criteria)
                ]
                
                all_handlers = handlers + matching_global
                
                if not all_handlers:
                    logger.debug(f"No handlers for event {event.type.value}")
                    continue
                
                # Execute all handlers
                for handler in all_handlers:
                    try:
                        await handler.handle(event)
                        self._stats["processed"] += 1
                    except Exception as e:
                        self._stats["errors"] += 1
                        logger.error(f"Error processing event: {e}", exc_info=True)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self._stats["errors"] += 1
                logger.error(f"Error in event processing loop: {e}", exc_info=True)
    
    async def start(self) -> None:
        """Start processing events asynchronously."""
        if self._running:
            logger.warning("EventBus is already running")
            return
        
        self._running = True
        logger.info("EventBus started")
        
        # Start event processing loop
        await self._process_events()
    
    def stop(self) -> None:
        """Stop processing events."""
        self._running = False
        logger.info("EventBus stopped")
    
    def get_stats(self) -> Dict[str, int]:
        """Get event bus statistics.
        
        Returns:
            Dictionary with published, processed, and error counts
        """
        return self._stats.copy()
    
    def reset_stats(self) -> None:
        """Reset event statistics."""
        self._stats = {
            "published": 0,
            "processed": 0,
            "errors": 0,
        }
    
    def get_subscriber_count(self, event_type: Optional[EventType] = None) -> int:
        """Get number of subscribers.
        
        Args:
            event_type: Optional specific event type. If None, returns total.
            
        Returns:
            Number of subscribers
        """
        if event_type:
            return len(self._subscribers.get(event_type, []))
        return sum(len(handlers) for handlers in self._subscribers.values()) + len(self._global_handlers)
    
    def __repr__(self) -> str:
        """String representation of EventBus."""
        total = self.get_subscriber_count()
        return f"EventBus(running={self._running}, subscribers={total}, stats={self._stats})"


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create the global event bus instance.
    
    Returns:
        The singleton EventBus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def reset_event_bus() -> None:
    """Reset the global event bus (mainly for testing)."""
    global _event_bus
    _event_bus = None
