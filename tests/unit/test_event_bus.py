"""Unit tests for EventBus."""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock




@pytest.fixture(autouse=True)
def clear_event_bus():
    """Clear event bus history before each test."""
    bus = get_event_bus()
    bus.clear_event_history()
    bus._subscribers.clear()
    bus._async_subscribers.clear()
    yield
    bus.clear_event_history()
    bus._subscribers.clear()
    bus._async_subscribers.clear()

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.event_bus import EventBus, Event, get_event_bus, publish_event, publish_event_async


class TestEvent:
    """Test cases for Event model."""

    def test_event_creation(self):
        """Test creating an Event."""
        event = Event(
            event_type="test_event",
            data={"key": "value"},
            correlation_id="test-correlation-id",
            timestamp="2023-01-01T00:00:00Z"
        )
        
        assert event.event_type == "test_event"
        assert event.data == {"key": "value"}
        assert event.correlation_id == "test-correlation-id"
        assert event.timestamp == "2023-01-01T00:00:00Z"

    def test_event_default_values(self):
        """Test Event creation with default values."""
        event = Event(event_type="test_event", data={"key": "value"})
        
        assert event.event_type == "test_event"
        assert event.data == {"key": "value"}
        assert event.correlation_id is None  # correlation_id is optional and defaults to None
        assert event.timestamp is not None


class TestEventBus:
    """Test cases for EventBus."""

    def test_singleton_pattern(self):
        """Test that EventBus is a singleton."""
        bus1 = EventBus()
        bus2 = EventBus()
        assert bus1 is bus2

    def test_initialization(self):
        """Test EventBus initialization."""
        bus = EventBus()
        assert hasattr(bus, '_subscribers')
        assert hasattr(bus, '_async_subscribers')
        assert hasattr(bus, '_event_history')
        assert hasattr(bus, '_lock')

    def test_subscribe_sync_callback(self):
        """Test subscribing a synchronous callback."""
        bus = EventBus()
        callback = Mock()
        
        bus.subscribe("test_event", callback)
        
        assert callback in bus._subscribers["test_event"]

    def test_subscribe_async_callback(self):
        """Test subscribing an asynchronous callback."""
        bus = EventBus()
        callback = AsyncMock()
        
        bus.subscribe_async("test_event", callback)
        
        assert callback in bus._async_subscribers["test_event"]

    def test_publish_sync_event(self):
        """Test publishing a synchronous event."""
        bus = EventBus()
        callback = Mock()
        bus.subscribe("test_event", callback)
        
        bus.publish("test_event", {"key": "value"})
        
        callback.assert_called_once()
        assert len(bus._event_history) == 1

    @pytest.mark.asyncio
    async def test_publish_async_event(self):
        """Test publishing an asynchronous event."""
        bus = EventBus()
        callback = AsyncMock()
        bus.subscribe_async("test_event", callback)
        
        await bus.publish_async("test_event", {"key": "value"})
        
        callback.assert_called_once()
        assert len(bus._event_history) == 1

    def test_publish_with_correlation_id(self):
        """Test publishing an event with correlation ID."""
        bus = EventBus()
        callback = Mock()
        bus.subscribe("test_event", callback)
        
        bus.publish("test_event", {"key": "value"}, "test-correlation-id")
        
        callback.assert_called_once()
        event = bus._event_history[0]
        assert event.correlation_id == "test-correlation-id"

    def test_multiple_subscribers(self):
        """Test multiple subscribers for the same event."""
        bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()
        
        bus.subscribe("test_event", callback1)
        bus.subscribe("test_event", callback2)
        
        bus.publish("test_event", {"key": "value"})
        
        callback1.assert_called_once()
        callback2.assert_called_once()

    def test_event_history(self):
        """Test that events are stored in history."""
        bus = EventBus()
        
        bus.publish("event1", {"data": "value1"})
        bus.publish("event2", {"data": "value2"})
        
        assert len(bus._event_history) == 2
        assert bus._event_history[0].event_type == "event1"
        assert bus._event_history[1].event_type == "event2"

    def test_get_event_history(self):
        """Test getting event history."""
        bus = EventBus()
        
        bus.publish("test_event", {"key": "value"})
        history = bus.get_event_history()
        
        assert len(history) == 1
        assert history[0].event_type == "test_event"

    def test_get_event_history_by_type(self):
        """Test getting event history filtered by type."""
        bus = EventBus()
        
        bus.publish("event1", {"data": "value1"})
        bus.publish("event2", {"data": "value2"})
        bus.publish("event1", {"data": "value3"})
        
        event1_history = bus.get_event_history("event1")
        assert len(event1_history) == 2
        assert all(event.event_type == "event1" for event in event1_history)

    def test_clear_event_history(self):
        """Test clearing event history."""
        bus = EventBus()
        
        bus.publish("test_event", {"key": "value"})
        assert len(bus._event_history) == 1
        
        bus.clear_event_history()
        assert len(bus._event_history) == 0

    def test_unsubscribe(self):
        """Test unsubscribing a callback."""
        bus = EventBus()
        callback = Mock()
        
        bus.subscribe("test_event", callback)
        assert callback in bus._subscribers["test_event"]
        
        bus.unsubscribe("test_event", callback)
        assert callback not in bus._subscribers["test_event"]

    def test_unsubscribe_async(self):
        """Test unsubscribing an async callback."""
        bus = EventBus()
        callback = AsyncMock()
        
        bus.subscribe_async("test_event", callback)
        assert callback in bus._async_subscribers["test_event"]
        
        bus.unsubscribe_async("test_event", callback)
        assert callback not in bus._async_subscribers["test_event"]

    def test_get_subscriber_count(self):
        """Test getting subscriber count."""
        bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()
        
        bus.subscribe("test_event", callback1)
        bus.subscribe("test_event", callback2)
        
        assert bus.get_subscriber_count("test_event") == 2

    def test_get_async_subscriber_count(self):
        """Test getting async subscriber count."""
        bus = EventBus()
        callback1 = AsyncMock()
        callback2 = AsyncMock()
        
        bus.subscribe_async("test_event", callback1)
        bus.subscribe_async("test_event", callback2)
        
        assert bus.get_async_subscriber_count("test_event") == 2

    def test_publish_to_nonexistent_event(self):
        """Test publishing to an event with no subscribers."""
        bus = EventBus()
        
        # Should not raise an exception
        bus.publish("nonexistent_event", {"key": "value"})
        
        # Event should still be in history
        assert len(bus._event_history) == 1

    @pytest.mark.asyncio
    async def test_publish_async_to_nonexistent_event(self):
        """Test publishing async to an event with no subscribers."""
        bus = EventBus()
        
        # Should not raise an exception
        await bus.publish_async("nonexistent_event", {"key": "value"})
        
        # Event should still be in history
        assert len(bus._event_history) == 1

    def test_callback_exception_handling(self):
        """Test that exceptions in callbacks don't break the event bus."""
        bus = EventBus()
        
        def failing_callback(event):
            raise Exception("Callback failed")
        
        bus.subscribe("test_event", failing_callback)
        
        # Should not raise an exception
        bus.publish("test_event", {"key": "value"})
        
        # Event should still be in history
        assert len(bus._event_history) == 1

    @pytest.mark.asyncio
    async def test_async_callback_exception_handling(self):
        """Test that exceptions in async callbacks don't break the event bus."""
        bus = EventBus()
        
        async def failing_async_callback(event):
            raise Exception("Async callback failed")
        
        bus.subscribe_async("test_event", failing_async_callback)
        
        # Should not raise an exception
        await bus.publish_async("test_event", {"key": "value"})
        
        # Event should still be in history
        assert len(bus._event_history) == 1


class TestEventBusHelpers:
    """Test cases for EventBus helper functions."""

    def test_get_event_bus(self):
        """Test get_event_bus helper function."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2

    def test_publish_event(self):
        """Test publish_event helper function."""
        bus = get_event_bus()
        callback = Mock()
        bus.subscribe("test_event", callback)
        
        publish_event("test_event", {"key": "value"})
        
        callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_event_async(self):
        """Test publish_event_async helper function."""
        bus = get_event_bus()
        callback = AsyncMock()
        bus.subscribe_async("test_event", callback)
        
        await publish_event_async("test_event", {"key": "value"})
        
        callback.assert_called_once()

    def test_publish_event_with_correlation_id(self):
        """Test publish_event with correlation ID."""
        bus = get_event_bus()
        callback = Mock()
        bus.subscribe("test_event", callback)
        
        publish_event("test_event", {"key": "value"}, "test-correlation-id")
        
        callback.assert_called_once()
        event = bus._event_history[0]
        assert event.correlation_id == "test-correlation-id" 