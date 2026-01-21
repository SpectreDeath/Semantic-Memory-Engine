"""
Tests for Event Bus system (events.py)

Comprehensive test suite for event-driven architecture.
Tests cover: creation, pub/sub, async handling, filtering, stats, and error handling.

Coverage target: >95%
Test cases: 20+
"""

import pytest
import asyncio
from datetime import datetime
from src.core.events import (
    EventType, Event, EventHandler, EventBus, 
    get_event_bus, reset_event_bus
)


# ============================================================================
# EVENT TESTS (5 cases)
# ============================================================================

class TestEvent:
    """Test Event dataclass functionality."""
    
    def test_event_creation(self):
        """Test basic event creation."""
        event = Event(
            type=EventType.SENTIMENT_ANALYZED,
            source="sentiment_analyzer",
            data={"sentiment": "positive", "score": 0.85}
        )
        
        assert event.type == EventType.SENTIMENT_ANALYZED
        assert event.source == "sentiment_analyzer"
        assert event.data["sentiment"] == "positive"
        assert event.data["score"] == 0.85
        assert event.id is not None
        assert event.timestamp is not None
    
    def test_event_with_metadata(self):
        """Test event with metadata."""
        event = Event(
            type=EventType.QUERY_EXECUTED,
            source="query_engine",
            data={"query": "test"},
            metadata={"request_id": "123", "user_id": "user456"}
        )
        
        assert event.metadata["request_id"] == "123"
        assert event.metadata["user_id"] == "user456"
    
    def test_event_invalid_source(self):
        """Test event creation fails with empty source."""
        with pytest.raises(ValueError):
            Event(
                type=EventType.SENTIMENT_ANALYZED,
                source="",
                data={}
            )
    
    def test_event_invalid_type(self):
        """Test event creation fails with invalid type."""
        with pytest.raises(TypeError):
            Event(
                type="not_an_enum",  # type: ignore
                source="test",
                data={}
            )
    
    def test_event_matches_filter(self):
        """Test event filtering functionality."""
        event = Event(
            type=EventType.SENTIMENT_ANALYZED,
            source="sentiment_analyzer",
            data={"sentiment": "positive", "score": 0.85},
            metadata={"request_id": "123"}
        )
        
        # Test exact type match
        assert event.matches_filter({"type": EventType.SENTIMENT_ANALYZED})
        
        # Test non-match
        assert not event.matches_filter({"type": EventType.QUERY_EXECUTED})
        
        # Test source match
        assert event.matches_filter({"source": "sentiment_analyzer"})
        
        # Test data field match
        assert event.matches_filter({"sentiment": "positive"})
        
        # Test metadata match
        assert event.matches_filter({"request_id": "123"})
        
        # Test multi-criteria match
        assert event.matches_filter({
            "type": EventType.SENTIMENT_ANALYZED,
            "source": "sentiment_analyzer",
            "sentiment": "positive"
        })
        
        # Test multi-criteria non-match
        assert not event.matches_filter({
            "type": EventType.SENTIMENT_ANALYZED,
            "sentiment": "negative"
        })


# ============================================================================
# EVENT HANDLER TESTS (3 cases)
# ============================================================================

class TestEventHandler:
    """Test EventHandler functionality."""
    
    def test_sync_handler_creation(self):
        """Test creating sync event handler."""
        def handler(event: Event):
            pass
        
        eh = EventHandler(handler, "test_handler")
        assert eh.name == "test_handler"
        assert eh.is_async is False
        assert eh.callback == handler
    
    def test_async_handler_creation(self):
        """Test creating async event handler."""
        async def handler(event: Event):
            pass
        
        eh = EventHandler(handler, "async_handler")
        assert eh.is_async is True
    
    @pytest.mark.asyncio
    async def test_handler_execution_error(self):
        """Test handler catches and logs errors."""
        def handler(event: Event):
            raise ValueError("Test error")
        
        eh = EventHandler(handler, "error_handler")
        event = Event(
            type=EventType.ERROR_OCCURRED,
            source="test",
            data={}
        )
        
        # Should not raise, error is caught
        await eh.handle(event)


# ============================================================================
# EVENT BUS TESTS (12 cases)
# ============================================================================

class TestEventBus:
    """Test EventBus core functionality."""
    
    @pytest.fixture
    def bus(self):
        """Provide a fresh event bus for each test."""
        reset_event_bus()
        return EventBus()
    
    def test_bus_creation(self, bus):
        """Test EventBus initialization."""
        assert bus._running is False
        assert len(bus._subscribers) == 0
        assert bus.get_subscriber_count() == 0
    
    def test_subscribe_handler(self, bus):
        """Test subscribing a handler."""
        call_count = 0
        
        def handler(event: Event):
            nonlocal call_count
            call_count += 1
        
        bus.subscribe(EventType.SENTIMENT_ANALYZED, handler)
        
        assert bus.get_subscriber_count() == 1
        assert bus.get_subscriber_count(EventType.SENTIMENT_ANALYZED) == 1
    
    def test_unsubscribe_handler(self, bus):
        """Test unsubscribing a handler."""
        def handler(event: Event):
            pass
        
        bus.subscribe(EventType.SENTIMENT_ANALYZED, handler)
        assert bus.get_subscriber_count() == 1
        
        result = bus.unsubscribe(EventType.SENTIMENT_ANALYZED, handler)
        assert result is True
        assert bus.get_subscriber_count() == 0
        
        # Unsubscribe non-existent handler
        result = bus.unsubscribe(EventType.SENTIMENT_ANALYZED, handler)
        assert result is False
    
    def test_publish_event(self, bus):
        """Test publishing an event."""
        event = Event(
            type=EventType.SENTIMENT_ANALYZED,
            source="test",
            data={"test": "data"}
        )
        
        bus.publish(event)
        
        assert bus._stats["published"] == 1
        assert bus._event_queue.qsize() == 1
    
    def test_publish_invalid_event(self, bus):
        """Test publishing non-Event object fails."""
        with pytest.raises(TypeError):
            bus.publish({"not": "an event"})  # type: ignore
    
    def test_stats_tracking(self, bus):
        """Test event statistics tracking."""
        assert bus.get_stats()["published"] == 0
        
        event = Event(
            type=EventType.SENTIMENT_ANALYZED,
            source="test",
            data={}
        )
        bus.publish(event)
        
        assert bus.get_stats()["published"] == 1
    
    def test_reset_stats(self, bus):
        """Test stats reset."""
        event = Event(
            type=EventType.SENTIMENT_ANALYZED,
            source="test",
            data={}
        )
        bus.publish(event)
        assert bus.get_stats()["published"] == 1
        
        bus.reset_stats()
        assert bus.get_stats()["published"] == 0
    
    def test_bus_string_representation(self, bus):
        """Test EventBus __repr__ method."""
        repr_str = repr(bus)
        assert "EventBus" in repr_str
        assert "running=False" in repr_str
    
    @pytest.mark.asyncio
    async def test_bus_start_stop(self, bus):
        """Test starting and stopping the bus."""
        # Start bus
        task = asyncio.create_task(bus.start())
        await asyncio.sleep(0.1)  # Let it start
        
        assert bus._running is True
        
        # Stop bus
        bus.stop()
        await asyncio.sleep(0.2)
        assert bus._running is False
        
        # Clean up task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass  # Expected
    
    def test_multiple_subscribers(self, bus):
        """Test multiple subscribers to same event."""
        def handler1(event: Event):
            pass
        
        def handler2(event: Event):
            pass
        
        def handler3(event: Event):
            pass
        
        bus.subscribe(EventType.SENTIMENT_ANALYZED, handler1)
        bus.subscribe(EventType.SENTIMENT_ANALYZED, handler2)
        bus.subscribe(EventType.QUERY_EXECUTED, handler3)
        
        assert bus.get_subscriber_count() == 3
        assert bus.get_subscriber_count(EventType.SENTIMENT_ANALYZED) == 2
        assert bus.get_subscriber_count(EventType.QUERY_EXECUTED) == 1


# ============================================================================
# ASYNC EVENT HANDLING TESTS (3 cases)
# ============================================================================

class TestAsyncEventHandling:
    """Test async event processing."""
    
    @pytest.mark.asyncio
    async def test_sync_handler_execution(self):
        """Test sync handler execution."""
        events_received = []
        
        def handler(event: Event):
            events_received.append(event)
        
        bus = EventBus()
        bus.subscribe(EventType.SENTIMENT_ANALYZED, handler)
        
        event = Event(
            type=EventType.SENTIMENT_ANALYZED,
            source="test",
            data={"result": "positive"}
        )
        
        # Start bus in background
        task = asyncio.create_task(bus.start())
        await asyncio.sleep(0.1)
        
        # Publish event
        bus.publish(event)
        await asyncio.sleep(0.2)  # Wait for processing
        
        # Verify handler was called
        assert len(events_received) == 1
        assert events_received[0].data["result"] == "positive"
        
        # Cleanup
        bus.stop()
        with pytest.raises(asyncio.CancelledError):
            task.cancel()
            await task
    
    @pytest.mark.asyncio
    async def test_async_handler_execution(self):
        """Test async handler execution."""
        events_received = []
        
        async def handler(event: Event):
            await asyncio.sleep(0.05)
            events_received.append(event)
        
        bus = EventBus()
        bus.subscribe(EventType.TEXT_SUMMARIZED, handler)
        
        event = Event(
            type=EventType.TEXT_SUMMARIZED,
            source="test",
            data={"summary": "test"}
        )
        
        # Start bus
        task = asyncio.create_task(bus.start())
        await asyncio.sleep(0.1)
        
        # Publish event
        bus.publish(event)
        await asyncio.sleep(0.3)  # Wait for async handler
        
        assert len(events_received) == 1
        
        # Cleanup
        bus.stop()
        with pytest.raises(asyncio.CancelledError):
            task.cancel()
            await task
    
    @pytest.mark.asyncio
    async def test_multiple_event_processing(self):
        """Test processing multiple events."""
        events_received = []
        
        def handler(event: Event):
            events_received.append(event)
        
        bus = EventBus()
        bus.subscribe(EventType.SENTIMENT_ANALYZED, handler)
        bus.subscribe(EventType.TEXT_SUMMARIZED, handler)
        
        # Start bus
        task = asyncio.create_task(bus.start())
        await asyncio.sleep(0.1)
        
        # Publish multiple events
        for i in range(5):
            event = Event(
                type=EventType.SENTIMENT_ANALYZED if i % 2 == 0 else EventType.TEXT_SUMMARIZED,
                source="test",
                data={"index": i}
            )
            bus.publish(event)
        
        await asyncio.sleep(0.3)
        
        assert len(events_received) == 5
        
        # Cleanup
        bus.stop()
        with pytest.raises(asyncio.CancelledError):
            task.cancel()
            await task


# ============================================================================
# EVENT FILTERING TESTS (2 cases)
# ============================================================================

class TestEventFiltering:
    """Test event filtering functionality."""
    
    @pytest.mark.asyncio
    async def test_filter_by_criteria(self):
        """Test subscribing with filter criteria."""
        events_received = []
        
        def handler(event: Event):
            events_received.append(event)
        
        bus = EventBus()
        
        # Subscribe with filter: only positive sentiments
        bus.subscribe(
            EventType.SENTIMENT_ANALYZED,
            handler,
            filter_criteria={"sentiment": "positive"}
        )
        
        # Start bus
        task = asyncio.create_task(bus.start())
        await asyncio.sleep(0.1)
        
        # Publish matching event
        event1 = Event(
            type=EventType.SENTIMENT_ANALYZED,
            source="test",
            data={"sentiment": "positive", "score": 0.9}
        )
        bus.publish(event1)
        
        # Publish non-matching event
        event2 = Event(
            type=EventType.SENTIMENT_ANALYZED,
            source="test",
            data={"sentiment": "negative", "score": 0.1}
        )
        bus.publish(event2)
        
        await asyncio.sleep(0.2)
        
        # Only matching event should be received
        assert len(events_received) == 1
        assert events_received[0].data["sentiment"] == "positive"
        
        # Cleanup
        bus.stop()
        with pytest.raises(asyncio.CancelledError):
            task.cancel()
            await task
    
    def test_filter_criteria_matching(self):
        """Test filter criteria matching logic."""
        event = Event(
            type=EventType.SENTIMENT_ANALYZED,
            source="analyzer",
            data={"sentiment": "positive", "score": 0.85},
            metadata={"user_id": "123"}
        )
        
        # Test various filter scenarios
        assert event.matches_filter({"sentiment": "positive"})
        assert event.matches_filter({"score": 0.85})
        assert event.matches_filter({"user_id": "123"})
        assert event.matches_filter({"source": "analyzer"})
        
        assert not event.matches_filter({"sentiment": "negative"})
        assert not event.matches_filter({"score": 0.5})
        assert not event.matches_filter({"user_id": "999"})


# ============================================================================
# GLOBAL EVENT BUS TESTS (2 cases)
# ============================================================================

class TestGlobalEventBus:
    """Test global event bus singleton."""
    
    def test_get_event_bus_singleton(self):
        """Test get_event_bus returns singleton."""
        reset_event_bus()
        
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        
        assert bus1 is bus2
    
    def test_reset_event_bus(self):
        """Test resetting event bus."""
        bus1 = get_event_bus()
        reset_event_bus()
        bus2 = get_event_bus()
        
        assert bus1 is not bus2


# ============================================================================
# INTEGRATION TESTS (2 cases)
# ============================================================================

class TestEventBusIntegration:
    """Test Event Bus integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_real_world_scenario(self):
        """Test realistic event flow: sentiment analysis."""
        results = {
            "events_received": [],
            "text_processed": []
        }
        
        def on_sentiment_analyzed(event: Event):
            results["events_received"].append(event)
        
        async def on_text_summarized(event: Event):
            await asyncio.sleep(0.01)
            results["text_processed"].append(event)
        
        bus = EventBus()
        bus.subscribe(EventType.SENTIMENT_ANALYZED, on_sentiment_analyzed)
        bus.subscribe(EventType.TEXT_SUMMARIZED, on_text_summarized)
        
        # Start bus
        task = asyncio.create_task(bus.start())
        await asyncio.sleep(0.1)
        
        # Simulate sentiment analysis workflow
        for text in ["Great!", "Not good", "Excellent!"]:
            sentiment = "positive" if "good" not in text.lower() or "not" not in text.lower() else "negative"
            sentiment = "positive" if any(word in text for word in ["great", "excellent"]) else sentiment
            
            event = Event(
                type=EventType.SENTIMENT_ANALYZED,
                source="sentiment_analyzer",
                data={"text": text, "sentiment": sentiment}
            )
            bus.publish(event)
        
        await asyncio.sleep(0.2)
        
        # Verify events were processed
        assert len(results["events_received"]) == 3
        assert bus.get_stats()["published"] == 3
        
        # Cleanup
        bus.stop()
        with pytest.raises(asyncio.CancelledError):
            task.cancel()
            await task
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test bus continues after handler errors."""
        processed = []
        
        def failing_handler(event: Event):
            raise RuntimeError("Handler failed")
        
        def working_handler(event: Event):
            processed.append(event)
        
        bus = EventBus()
        bus.subscribe(EventType.SENTIMENT_ANALYZED, failing_handler)
        bus.subscribe(EventType.SENTIMENT_ANALYZED, working_handler)
        
        # Start bus
        task = asyncio.create_task(bus.start())
        await asyncio.sleep(0.1)
        
        # Publish event
        event = Event(
            type=EventType.SENTIMENT_ANALYZED,
            source="test",
            data={"test": "data"}
        )
        bus.publish(event)
        await asyncio.sleep(0.3)
        
        # Working handler should still process despite failing handler
        assert len(processed) == 1
        # Errors may have been logged
        
        # Cleanup
        bus.stop()
        await asyncio.sleep(0.1)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass  # Expected
