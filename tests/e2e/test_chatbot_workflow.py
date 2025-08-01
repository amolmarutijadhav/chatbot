"""End-to-end tests for complete chatbot workflows."""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.config_manager import ConfigurationManager
from utils.event_bus import EventBus, get_event_bus
from utils.logger import setup_logging, get_logger
from core.session_manager import SessionManager
from core.context_manager import ContextManager
from core.models import Session, Context, Message, Response, ChatRequest, ChatResponse


@pytest.fixture
def e2e_config():
    """Create a comprehensive E2E test configuration."""
    return {
        "chatbot": {
            "name": "Test Chatbot",
            "version": "1.0.0"
        },
        "session": {
            "max_sessions_per_user": 3,
            "timeout": 3600,
            "cleanup_interval": 300
        },
        "logging": {
            "level": "INFO",
            "structured": True,
            "console_output": True
        },
        "api": {
            "host": "localhost",
            "port": 8000
        }
    }


@pytest.fixture
def e2e_session_manager(e2e_config):
    """Create a session manager for E2E testing."""
    return SessionManager(e2e_config["session"])


@pytest.fixture
def e2e_context_manager(e2e_session_manager):
    """Create a context manager for E2E testing."""
    return ContextManager(e2e_session_manager)


@pytest.fixture
def e2e_event_bus():
    """Get the event bus for E2E testing."""
    return get_event_bus()


class TestCompleteChatWorkflow:
    """Test complete chat workflow from start to finish."""
    
    @pytest.mark.asyncio
    async def test_basic_chat_conversation(self, e2e_session_manager, e2e_context_manager, e2e_event_bus):
        """Test a complete basic chat conversation workflow."""
        # Setup
        await e2e_session_manager.start()
        e2e_event_bus.clear_event_history()
        
        try:
            # 1. User starts a new session
            session = await e2e_session_manager.create_session("alice")
            assert session is not None
            assert session.user_id == "alice"
            
            # 2. User sends first message
            context1 = await e2e_context_manager.build_context(
                session_id=session.session_id,
                message="Hello, how are you?",
                message_type="chat"
            )
            
            # 3. Verify context was built correctly
            assert context1.session_id == session.session_id
            assert context1.user_id == "alice"
            assert context1.message == "Hello, how are you?"
            assert context1.correlation_id is not None
            
            # 4. Simulate assistant response
            assistant_response = Message(
                content="Hello! I'm doing well, thank you for asking. How can I help you today?",
                role="assistant"
            )
            context1 = await e2e_context_manager.add_message_to_context(context1, assistant_response)
            
            # 5. User sends follow-up message
            context2 = await e2e_context_manager.build_context(
                session_id=session.session_id,
                message="Can you help me with a programming question?",
                message_type="chat"
            )
            
            # 6. Verify message history is maintained
            assert len(context2.message_history) == 3  # Initial + assistant + new user message
            
            # 7. Simulate assistant response
            assistant_response2 = Message(
                content="Of course! I'd be happy to help with your programming question. What would you like to know?",
                role="assistant"
            )
            context2 = await e2e_context_manager.add_message_to_context(context2, assistant_response2)
            
            # 8. Verify context has all messages
            assert len(context2.message_history) == 4  # All messages should be in context
            
            # 9. Verify events were published
            events = e2e_event_bus.get_event_history()
            session_events = [e for e in events if e.event_type == "session_created"]
            context_events = [e for e in events if e.event_type == "context_built"]
            assert len(session_events) == 1
            assert len(context_events) == 2  # Two context builds
            
        finally:
            await e2e_session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_mcp_request_workflow(self, e2e_session_manager, e2e_context_manager):
        """Test workflow for MCP (Model Context Protocol) requests."""
        await e2e_session_manager.start()
        try:
            # 1. Create session
            session = await e2e_session_manager.create_session("bob")
            
            # 2. User sends MCP request
            context = await e2e_context_manager.build_context(
                session_id=session.session_id,
                message="Please list the files in my current directory",
                message_type="mcp_request"
            )
            
            # 3. Verify MCP context is detected
            assert context.message_type == "mcp_request"
            assert e2e_context_manager.should_use_mcp(context) is True
            
            # 4. Get suggested MCP servers
            suggested_servers = e2e_context_manager.get_suggested_mcp_servers(context)
            assert "file_system" in suggested_servers
            
            # 5. Update context with MCP response
            mcp_response = Message(
                content="Found 5 files: file1.txt, file2.py, config.json, README.md, test.py",
                role="assistant"
            )
            context = await e2e_context_manager.add_message_to_context(context, mcp_response)
            
            # 6. Update MCP context
            mcp_updates = {
                "mcp_context": {
                    "file_system": {
                        "last_operation": "list_directory",
                        "files_found": 5,
                        "status": "success"
                    }
                }
            }
            context = await e2e_context_manager.update_context(context, mcp_updates)
            
            # 7. Verify MCP context was updated
            assert context.mcp_context["file_system"]["last_operation"] == "list_directory"
            assert context.mcp_context["file_system"]["files_found"] == 5
            
        finally:
            await e2e_session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_multi_session_user_workflow(self, e2e_session_manager, e2e_context_manager):
        """Test workflow with multiple sessions for the same user."""
        await e2e_session_manager.start()
        try:
            # 1. Create multiple sessions for same user
            session1 = await e2e_session_manager.create_session("charlie")
            session2 = await e2e_session_manager.create_session("charlie")
            
            # 2. Send messages to different sessions
            context1 = await e2e_context_manager.build_context(
                session_id=session1.session_id,
                message="This is session 1",
                message_type="chat"
            )
            
            context2 = await e2e_context_manager.build_context(
                session_id=session2.session_id,
                message="This is session 2",
                message_type="chat"
            )
            
            # 3. Verify sessions are independent
            assert context1.session_id != context2.session_id
            assert context1.message != context2.message
            
            # 4. Verify session statistics
            stats = e2e_session_manager.get_session_stats()
            assert stats["unique_users"] == 1
            assert stats["user_session_counts"]["charlie"] == 2
            
            # 5. Create third session (limit is 3, so this should be fine)
            session3 = await e2e_session_manager.create_session("charlie")
            
            # 6. Create fourth session (should trigger cleanup of oldest)
            session4 = await e2e_session_manager.create_session("charlie")
            
            # 7. Verify oldest session was closed (set to inactive)
            old_session = await e2e_session_manager.get_session(session1.session_id)
            # The session should be None because it's inactive
            assert old_session is None
            
            # Check active session count
            stats = e2e_session_manager.get_session_stats()
            assert stats["active_sessions"] == 3  # Only 3 active sessions (limit)
            
            # 8. Verify newer sessions still exist
            assert await e2e_session_manager.get_session(session2.session_id) is not None
            assert await e2e_session_manager.get_session(session3.session_id) is not None
            assert await e2e_session_manager.get_session(session4.session_id) is not None
            
        finally:
            await e2e_session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_session_expiration_workflow(self, e2e_session_manager, e2e_context_manager):
        """Test workflow with session expiration."""
        await e2e_session_manager.start()
        try:
            # 1. Create session
            session = await e2e_session_manager.create_session("david")
            
            # 2. Send initial message
            context = await e2e_context_manager.build_context(
                session_id=session.session_id,
                message="Hello",
                message_type="chat"
            )
            
            # 3. Manually expire the session
            session.is_active = False
            session.last_activity = session.last_activity.replace(year=2020)  # Old date
            
            # 4. Try to build context with expired session
            with pytest.raises(ValueError, match="Session.*not found"):
                await e2e_context_manager.build_context(
                    session_id=session.session_id,
                    message="This should fail",
                    message_type="chat"
                )
            
            # 5. Force cleanup
            await e2e_session_manager._cleanup_expired_sessions()
            
            # 6. Verify session is gone
            expired_session = await e2e_session_manager.get_session(session.session_id)
            assert expired_session is None
            
        finally:
            await e2e_session_manager.stop()


class TestErrorRecoveryWorkflow:
    """Test error recovery and resilience workflows."""
    
    @pytest.mark.asyncio
    async def test_invalid_session_recovery(self, e2e_session_manager, e2e_context_manager):
        """Test recovery from invalid session scenarios."""
        await e2e_session_manager.start()
        try:
            # 1. Try to use non-existent session
            with pytest.raises(ValueError):
                await e2e_context_manager.build_context(
                    session_id="non-existent-session",
                    message="This should fail",
                    message_type="chat"
                )
            
            # 2. Create a new session (recovery)
            session = await e2e_session_manager.create_session("recovery_user")
            
            # 3. Verify new session works
            context = await e2e_context_manager.build_context(
                session_id=session.session_id,
                message="Recovery successful",
                message_type="chat"
            )
            
            assert context.session_id == session.session_id
            assert context.user_id == "recovery_user"
            
        finally:
            await e2e_session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_session_limit_recovery(self, e2e_session_manager):
        """Test recovery when session limits are reached."""
        await e2e_session_manager.start()
        try:
            # 1. Set low limit
            e2e_session_manager.max_sessions_per_user = 2
            
            # 2. Create sessions up to limit
            session1 = await e2e_session_manager.create_session("limit_user")
            session2 = await e2e_session_manager.create_session("limit_user")
            
            # 3. Create third session (should close oldest)
            session3 = await e2e_session_manager.create_session("limit_user")
            
            # 4. Verify recovery worked
            assert await e2e_session_manager.get_session(session1.session_id) is None
            assert await e2e_session_manager.get_session(session2.session_id) is not None
            assert await e2e_session_manager.get_session(session3.session_id) is not None
            
        finally:
            await e2e_session_manager.stop()


class TestPerformanceWorkflow:
    """Test performance characteristics of complete workflows."""
    
    @pytest.mark.asyncio
    async def test_concurrent_user_workflow(self, e2e_session_manager, e2e_context_manager):
        """Test concurrent user workflows."""
        await e2e_session_manager.start()
        try:
            # Define workflow for a single user
            async def user_workflow(user_id):
                # Create session
                session = await e2e_session_manager.create_session(f"user_{user_id}")
                
                # Send message
                context = await e2e_context_manager.build_context(
                    session_id=session.session_id,
                    message=f"Message from user {user_id}",
                    message_type="chat"
                )
                
                # Add response
                response = Message(
                    content=f"Response to user {user_id}",
                    role="assistant"
                )
                context = await e2e_context_manager.add_message_to_context(context, response)
                
                return session.session_id
            
            # Run 5 concurrent user workflows
            tasks = [user_workflow(i) for i in range(5)]
            session_ids = await asyncio.gather(*tasks)
            
            # Verify all workflows completed
            assert len(session_ids) == 5
            assert len(set(session_ids)) == 5  # All unique
            
            # Verify session count
            assert e2e_session_manager.get_session_count() == 5
            
        finally:
            await e2e_session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_rapid_message_workflow(self, e2e_session_manager, e2e_context_manager):
        """Test rapid message processing workflow."""
        await e2e_session_manager.start()
        try:
            # Create session
            session = await e2e_session_manager.create_session("rapid_user")
            
            # Send many messages rapidly
            contexts = []
            for i in range(10):
                context = await e2e_context_manager.build_context(
                    session_id=session.session_id,
                    message=f"Rapid message {i}",
                    message_type="chat"
                )
                contexts.append(context)
                
                # Add response
                response = Message(
                    content=f"Response {i}",
                    role="assistant"
                )
                context = await e2e_context_manager.add_message_to_context(context, response)
            
            # Verify all contexts were created
            assert len(contexts) == 10
            
            # Verify context has all messages
            assert len(context.message_history) == 20  # 10 user + 10 assistant messages
            
        finally:
            await e2e_session_manager.stop()


class TestDataPersistenceWorkflow:
    """Test data persistence and consistency workflows."""
    
    @pytest.mark.asyncio
    async def test_context_persistence_workflow(self, e2e_session_manager, e2e_context_manager):
        """Test that context data persists correctly across operations."""
        await e2e_session_manager.start()
        try:
            # 1. Create session and context
            session = await e2e_session_manager.create_session("persistence_user")
            context = await e2e_context_manager.build_context(
                session_id=session.session_id,
                message="Initial message",
                message_type="chat"
            )
            
            # 2. Add metadata and context data
            updates = {
                "mcp_context": {"server1": {"status": "active", "last_used": "2024-01-01"}},
                "llm_context": {"provider": "openai", "model": "gpt-4"},
                "metadata": {"source": "web", "user_agent": "test-browser"}
            }
            context = await e2e_context_manager.update_context(context, updates)
            
            # 3. Add messages
            message1 = Message(content="User message", role="user")
            message2 = Message(content="Assistant response", role="assistant")
            
            context = await e2e_context_manager.add_message_to_context(context, message1)
            context = await e2e_context_manager.add_message_to_context(context, message2)
            
            # 4. Verify context data was updated correctly
            assert context.mcp_context["server1"]["status"] == "active"
            assert context.llm_context["provider"] == "openai"
            assert context.llm_context["model"] == "gpt-4"
            assert len(context.message_history) == 3  # Initial + 2 added messages (correct count)
            
        finally:
            await e2e_session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_session_metadata_persistence(self, e2e_session_manager):
        """Test that session metadata persists correctly."""
        await e2e_session_manager.start()
        try:
            # 1. Create session
            session = await e2e_session_manager.create_session("metadata_user")
            
            # 2. Update session metadata
            session.set_metadata("browser", "chrome")
            session.set_metadata("ip_address", "192.168.1.1")
            session.set_metadata("user_agent", "Mozilla/5.0")
            
            # 3. Add MCP server
            session.add_mcp_server("file_system")
            session.add_mcp_server("database")
            
            # 4. Update session
            await e2e_session_manager.update_session(session.session_id, {
                "metadata": session.metadata,
                "mcp_servers": session.mcp_servers
            })
            
            # 5. Retrieve and verify persistence
            updated_session = await e2e_session_manager.get_session(session.session_id)
            assert updated_session.metadata["browser"] == "chrome"
            assert updated_session.metadata["ip_address"] == "192.168.1.1"
            assert updated_session.metadata["user_agent"] == "Mozilla/5.0"
            assert "file_system" in updated_session.mcp_servers
            assert "database" in updated_session.mcp_servers
            
        finally:
            await e2e_session_manager.stop() 