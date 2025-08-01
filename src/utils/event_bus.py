"""Event bus system for loose coupling between components."""

import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from collections import defaultdict
import asyncio
import logging

logger = logging.getLogger(__name__)


class Event:
    """Event representation."""
    
    def __init__(self, event_type: str, data: Any, timestamp: Optional[datetime] = None, correlation_id: Optional[str] = None):
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or datetime.utcnow()
        self.id = str(uuid.uuid4())
        self.correlation_id = correlation_id
    
    def __str__(self) -> str:
        return f"Event(id={self.id}, type={self.event_type}, timestamp={self.timestamp})"
    
    def __repr__(self) -> str:
        return f"Event(id={self.id}, type={self.event_type}, data={self.data}, timestamp={self.timestamp})"


class EventBus:
    """Central event bus for system-wide communication."""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
            self._event_history: List[Event] = []
            self._max_history_size = 1000
            self._async_subscribers: Dict[str, List[Callable]] = defaultdict(list)
            self._lock = asyncio.Lock()
            self._initialized = True
    
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type."""
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to event type: {event_type}")
    
    def subscribe_async(self, event_type: str, callback: Callable):
        """Subscribe to an event type with async callback."""
        self._async_subscribers[event_type].append(callback)
        logger.debug(f"Subscribed async to event type: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from an event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from event type: {event_type}")
            except ValueError:
                logger.warning(f"Callback not found for event type: {event_type}")
        
        if event_type in self._async_subscribers:
            try:
                self._async_subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed async from event type: {event_type}")
            except ValueError:
                logger.warning(f"Async callback not found for event type: {event_type}")
    
    def publish(self, event_type: str, data: Any, correlation_id: Optional[str] = None):
        """Publish an event to all subscribers."""
        event = Event(event_type, data, correlation_id=correlation_id)
        
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history_size:
            self._event_history.pop(0)
        
        # Notify synchronous subscribers
        for callback in self._subscribers[event_type]:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
        
        # Schedule async subscribers if event loop is running
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self._notify_async_subscribers(event))
        except RuntimeError:
            # No event loop running, skip async subscribers
            pass
        
        logger.debug(f"Published event: {event}")
    
    async def publish_async(self, event_type: str, data: Any, correlation_id: Optional[str] = None):
        """Publish an event asynchronously."""
        event = Event(event_type, data, correlation_id=correlation_id)
        
        # Add to history
        async with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history_size:
                self._event_history.pop(0)
        
        # Notify synchronous subscribers
        for callback in self._subscribers[event_type]:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
        
        # Notify async subscribers
        await self._notify_async_subscribers(event)
        
        logger.debug(f"Published async event: {event}")
    
    async def _notify_async_subscribers(self, event: Event):
        """Notify async subscribers of an event."""
        if event.event_type in self._async_subscribers:
            tasks = []
            for callback in self._async_subscribers[event.event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        task = asyncio.create_task(callback(event))
                        tasks.append(task)
                    else:
                        # If it's not a coroutine function, run it in executor
                        loop = asyncio.get_event_loop()
                        task = loop.run_in_executor(None, callback, event)
                        tasks.append(task)
                except Exception as e:
                    logger.error(f"Error scheduling async event handler for {event.event_type}: {e}")
            
            if tasks:
                try:
                    await asyncio.gather(*tasks, return_exceptions=True)
                except Exception as e:
                    logger.error(f"Error in async event handlers for {event.event_type}: {e}")
    
    def get_subscribers(self, event_type: str) -> List[Callable]:
        """Get all subscribers for an event type."""
        return self._subscribers[event_type].copy()
    
    def get_async_subscribers(self, event_type: str) -> List[Callable]:
        """Get all async subscribers for an event type."""
        return self._async_subscribers[event_type].copy()
    
    def get_event_history(self, event_type: Optional[str] = None, limit: Optional[int] = None) -> List[Event]:
        """Get event history, optionally filtered by type."""
        if event_type:
            history = [event for event in self._event_history if event.event_type == event_type]
        else:
            history = self._event_history.copy()
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def clear_history(self):
        """Clear event history."""
        self._event_history.clear()
        logger.debug("Event history cleared")
    
    def get_event_types(self) -> List[str]:
        """Get all registered event types."""
        all_types = set(self._subscribers.keys())
        all_types.update(self._async_subscribers.keys())
        return list(all_types)
    
    def get_subscriber_count(self, event_type: str) -> int:
        """Get the number of subscribers for an event type."""
        sync_count = len(self._subscribers.get(event_type, []))
        async_count = len(self._async_subscribers.get(event_type, []))
        return sync_count + async_count
    
    def get_async_subscriber_count(self, event_type: str) -> int:
        """Get the number of async subscribers for an event type."""
        return len(self._async_subscribers.get(event_type, []))
    
    def unsubscribe_async(self, event_type: str, callback: Callable):
        """Unsubscribe an async callback from an event type."""
        if event_type in self._async_subscribers:
            try:
                self._async_subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed async from event type: {event_type}")
            except ValueError:
                logger.warning(f"Async callback not found for event type: {event_type}")
    
    def clear_event_history(self):
        """Clear the event history."""
        self._event_history.clear()
    
    def __str__(self) -> str:
        return f"EventBus(subscribers={len(self._subscribers)}, async_subscribers={len(self._async_subscribers)})"
    
    def __repr__(self) -> str:
        return f"EventBus(event_types={self.get_event_types()}, history_size={len(self._event_history)})"


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def publish_event(event_type: str, data: Any, correlation_id: Optional[str] = None):
    """Publish an event using the global event bus."""
    event_bus = get_event_bus()
    event_bus.publish(event_type, data, correlation_id)


async def publish_event_async(event_type: str, data: Any, correlation_id: Optional[str] = None):
    """Publish an event asynchronously using the global event bus."""
    event_bus = get_event_bus()
    await event_bus.publish_async(event_type, data, correlation_id) 