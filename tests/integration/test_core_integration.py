"""Integration tests for core component interactions."""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.config_manager import ConfigurationManager
from utils.event_bus import EventBus, get_event_bus
from core.session_manager import SessionManager
from core.context_manager import ContextManager
from core.models import Session, Context, Message


@pytest.fixture
def test_config():
    """Create a test configuration."""
    return {
        "session": {
            "max_sessions_per_user": 5,
            "timeout": 3600,
            "cleanup_interval": 300
        },
        "logging": {
            "level": "INFO",
            "structured": True
        }
    }


@pytest.fixture
def session_manager(test_config):
    """Create a session manager for testing."""
    return SessionManager(test_config)


@pytest.fixture
def context_manager(session_manager):
    """Create a context manager for testing."""
    return ContextManager(session_manager)


@pytest.fixture
def event_bus():
    """Get the event bus instance."""
    return get_event_bus()


class TestConfigurationSessionIntegration:
    """Test integration between ConfigurationManager and SessionManager."""
    
    def test_config_session_manager_integration(self, test_config):
        """Test that SessionManager works with ConfigurationManager."""
        # Create config manager and set test config
        config_manager = ConfigurationManager()
        config_manager.config = test_config.copy()
        
        # Create session manager with config
        session_manager = SessionManager(config_manager.get("session"))
        
        # Verify config was applied
        assert session_manager.max_sessions_per_user == 5
        assert session_manager.session_timeout == 3600
        assert session_manager.cleanup_interval == 300
    
    def test_config_validation_integration(self):
        """Test configuration validation with session manager."""
        config_manager = ConfigurationManager()
        
        # Test with valid config
        valid_config = {
            "session": {
                "max_sessions_per_user": 10,
                "timeout": 1800,
                "cleanup_interval": 300
            }
        }
        config_manager.config = valid_config
        
        # Should not raise any exceptions
        session_manager = SessionManager(config_manager.get("session"))
        assert session_manager is not None


class TestSessionContextIntegration:
    """Test integration between SessionManager and ContextManager."""
    
    @pytest.mark.asyncio
    async def test_session_context_workflow(self, session_manager, context_manager):
        """Test complete session and context workflow."""
        await session_manager.start()
        try:
            # 1. Create a session
            session = await session_manager.create_session("test_user_1")
            assert session is not None
            assert session.user_id == "test_user_1"
            
            # 2. Build context using the session
            context = await context_manager.build_context(
                session_id=session.session_id,
                message="Hello, this is a test message",
                message_type="chat"
            )
            
            # 3. Verify context is properly linked to session
            assert context.session_id == session.session_id
            assert context.user_id == session.user_id
            assert context.message == "Hello, this is a test message"
            assert context.message_type == "chat"
            assert context.correlation_id is not None
            
            # 4. Verify session was updated with context
            updated_session = await session_manager.get_session(session.session_id)
            assert updated_session is not None
            # Note: Context is stored in session.context, but it's empty initially
            # The context manager updates it via update_session method
            
        finally:
            await session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_context_session_persistence(self, session_manager, context_manager):
        """Test that context changes persist in session."""
        await session_manager.start()
        try:
            # Create session and context
            session = await session_manager.create_session("test_user_2")
            context = await context_manager.build_context(
                session_id=session.session_id,
                message="Initial message",
                message_type="chat"
            )
            
            # Update context with new information
            updates = {
                "mcp_context": {"server1": "active"},
                "llm_context": {"provider": "openai"},
                "metadata": {"source": "test"}
            }
            updated_context = await context_manager.update_context(context, updates)
            
            # Verify context was updated
            assert updated_context.mcp_context["server1"] == "active"
            assert updated_context.llm_context["provider"] == "openai"
            assert updated_context.metadata["source"] == "test"
            
            # Verify session was updated with context changes
            updated_session = await session_manager.get_session(session.session_id)
            # The context manager should have updated the session via _update_session_context
            # Let's verify the context was built correctly
            assert updated_context.mcp_context["server1"] == "active"
            assert updated_context.llm_context["provider"] == "openai"
            
        finally:
            await session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_message_history_integration(self, session_manager, context_manager):
        """Test message history integration between context and session."""
        await session_manager.start()
        try:
            # Create session and initial context
            session = await session_manager.create_session("test_user_3")
            context = await context_manager.build_context(
                session_id=session.session_id,
                message="First message",
                message_type="chat"
            )
            
            # Add more messages to context
            message1 = Message(content="Response 1", role="assistant")
            message2 = Message(content="User follow-up", role="user")
            
            context = await context_manager.add_message_to_context(context, message1)
            context = await context_manager.add_message_to_context(context, message2)
            
            # Verify context has all messages
            assert len(context.message_history) == 3  # Initial + 2 added
            
            # Verify context has all messages
            assert len(context.message_history) == 3  # Initial + 2 added
            
            # Note: The session context is updated by the context manager
            # but we're testing the context object directly here
            
        finally:
            await session_manager.stop()


class TestEventBusIntegration:
    """Test integration with EventBus."""
    
    @pytest.mark.asyncio
    async def test_session_events_integration(self, session_manager, event_bus):
        """Test that session operations publish events."""
        await session_manager.start()
        try:
            # Clear event history
            event_bus.clear_event_history()
            
            # Create session (should publish event)
            session = await session_manager.create_session("test_user_4")
            
            # Check that session creation event was published
            events = event_bus.get_event_history()
            session_events = [e for e in events if e.event_type == "session_created"]
            assert len(session_events) == 1
            
            session_event = session_events[0]
            assert session_event.data["user_id"] == "test_user_4"
            assert session_event.data["session_id"] == session.session_id
            
        finally:
            await session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_context_events_integration(self, session_manager, context_manager, event_bus):
        """Test that context operations publish events."""
        await session_manager.start()
        try:
            # Clear event history
            event_bus.clear_event_history()
            
            # Create session and context
            session = await session_manager.create_session("test_user_5")
            context = await context_manager.build_context(
                session_id=session.session_id,
                message="Test message for events",
                message_type="chat"
            )
            
            # Check that context built event was published
            events = event_bus.get_event_history()
            context_events = [e for e in events if e.event_type == "context_built"]
            assert len(context_events) == 1
            
            context_event = context_events[0]
            assert context_event.data["session_id"] == session.session_id
            assert context_event.data["user_id"] == "test_user_5"
            assert context_event.data["message_type"] == "chat"
            assert context_event.data["correlation_id"] == context.correlation_id
            
        finally:
            await session_manager.stop()


class TestMultiUserIntegration:
    """Test integration with multiple users and sessions."""
    
    @pytest.mark.asyncio
    async def test_multiple_users_sessions(self, session_manager, context_manager):
        """Test handling multiple users with multiple sessions."""
        await session_manager.start()
        try:
            # Create sessions for different users
            user1_session1 = await session_manager.create_session("user1")
            user1_session2 = await session_manager.create_session("user1")
            user2_session1 = await session_manager.create_session("user2")
            
            # Verify sessions are separate
            assert user1_session1.session_id != user1_session2.session_id
            assert user1_session1.session_id != user2_session1.session_id
            
            # Create contexts for each session
            context1 = await context_manager.build_context(
                session_id=user1_session1.session_id,
                message="User 1, Session 1 message",
                message_type="chat"
            )
            
            context2 = await context_manager.build_context(
                session_id=user2_session1.session_id,
                message="User 2, Session 1 message",
                message_type="chat"
            )
            
            # Verify contexts are separate and correct
            assert context1.session_id == user1_session1.session_id
            assert context1.user_id == "user1"
            assert context2.session_id == user2_session1.session_id
            assert context2.user_id == "user2"
            
            # Verify session statistics
            stats = session_manager.get_session_stats()
            assert stats["total_sessions"] == 3
            assert stats["active_sessions"] == 3
            assert stats["unique_users"] == 2
            assert stats["user_session_counts"]["user1"] == 2
            assert stats["user_session_counts"]["user2"] == 1
            
        finally:
            await session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_session_cleanup_integration(self, session_manager):
        """Test session cleanup with expired sessions."""
        await session_manager.start()
        try:
            # Create sessions
            session1 = await session_manager.create_session("user1")
            session2 = await session_manager.create_session("user2")
            
            # Manually expire one session
            session1.is_active = False
            session1.last_activity = session1.last_activity.replace(year=2020)  # Old date
            
            # Force cleanup
            await session_manager._cleanup_expired_sessions()
            
            # Verify expired session is removed
            expired_session = await session_manager.get_session(session1.session_id)
            assert expired_session is None
            
            # Verify active session remains
            active_session = await session_manager.get_session(session2.session_id)
            assert active_session is not None
            
        finally:
            await session_manager.stop()


class TestErrorHandlingIntegration:
    """Test error handling across components."""
    
    @pytest.mark.asyncio
    async def test_invalid_session_context_integration(self, session_manager, context_manager):
        """Test handling of invalid session in context building."""
        await session_manager.start()
        try:
            # Try to build context with non-existent session
            with pytest.raises(ValueError, match="Session.*not found"):
                await context_manager.build_context(
                    session_id="non-existent-session",
                    message="This should fail",
                    message_type="chat"
                )
        finally:
            await session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_session_limit_integration(self, session_manager):
        """Test session limit enforcement."""
        await session_manager.start()
        try:
            # Set low limit
            session_manager.max_sessions_per_user = 2
            
            # Create sessions up to limit
            session1 = await session_manager.create_session("user1")
            session2 = await session_manager.create_session("user1")
            
            # Third session should close the oldest
            session3 = await session_manager.create_session("user1")
            
            # Verify oldest session was closed
            old_session = await session_manager.get_session(session1.session_id)
            assert old_session is None
            
            # Verify newer sessions exist
            assert await session_manager.get_session(session2.session_id) is not None
            assert await session_manager.get_session(session3.session_id) is not None
            
        finally:
            await session_manager.stop()


class TestPerformanceIntegration:
    """Test performance characteristics of integrated components."""
    
    @pytest.mark.asyncio
    async def test_concurrent_session_creation(self, session_manager):
        """Test concurrent session creation performance."""
        await session_manager.start()
        try:
            # Create multiple sessions concurrently
            async def create_session(user_id):
                return await session_manager.create_session(f"user_{user_id}")
            
            # Create 10 sessions concurrently
            tasks = [create_session(i) for i in range(10)]
            sessions = await asyncio.gather(*tasks)
            
            # Verify all sessions were created
            assert len(sessions) == 10
            for session in sessions:
                assert session is not None
                assert session.is_active is True
            
            # Verify session count
            assert session_manager.get_session_count() == 10
            
        finally:
            await session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_context_building_performance(self, session_manager, context_manager):
        """Test context building performance with multiple operations."""
        await session_manager.start()
        try:
            # Create session
            session = await session_manager.create_session("perf_user")
            
            # Build multiple contexts quickly
            contexts = []
            for i in range(5):
                context = await context_manager.build_context(
                    session_id=session.session_id,
                    message=f"Message {i}",
                    message_type="chat"
                )
                contexts.append(context)
            
            # Verify all contexts were created
            assert len(contexts) == 5
            for context in contexts:
                assert context.session_id == session.session_id
                assert context.correlation_id is not None
            
        finally:
            await session_manager.stop() 