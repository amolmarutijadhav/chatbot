"""Unit tests for SessionManager."""

import pytest
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.session_manager import SessionManager
from core.models import Session


@pytest.fixture
def session_config():
    """Test configuration for session manager."""
    return {
        "max_sessions_per_user": 3,
        "timeout": 3600,
        "cleanup_interval": 300
    }


@pytest.fixture
def session_manager(session_config):
    """Create a session manager for testing."""
    return SessionManager(session_config)


class TestSessionManager:
    """Test cases for SessionManager."""
    
    @pytest.mark.asyncio
    async def test_create_session(self, session_manager):
        await session_manager.start()
        try:
            session = await session_manager.create_session("test_user")
            assert session is not None
            assert session.user_id == "test_user"
            assert session.is_active is True
            assert session.session_id in session_manager.sessions
        finally:
            await session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_get_session(self, session_manager):
        await session_manager.start()
        try:
            created_session = await session_manager.create_session("test_user")
            retrieved_session = await session_manager.get_session(created_session.session_id)
            
            assert retrieved_session is not None
            assert retrieved_session.session_id == created_session.session_id
            assert retrieved_session.user_id == created_session.user_id
        finally:
            await session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, session_manager):
        await session_manager.start()
        try:
            session = await session_manager.get_session("nonexistent_id")
            assert session is None
        finally:
            await session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_close_session(self, session_manager):
        await session_manager.start()
        try:
            session = await session_manager.create_session("test_user")
            result = await session_manager.close_session(session.session_id)
            
            assert result is True
            assert session.is_active is False
        finally:
            await session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_max_sessions_per_user(self, session_manager):
        await session_manager.start()
        try:
            # Create maximum allowed sessions
            sessions = []
            for i in range(3):
                session = await session_manager.create_session("test_user")
                sessions.append(session)
            
            # Create one more session (should close the oldest)
            new_session = await session_manager.create_session("test_user")
            
            # Check that we still have 3 sessions
            user_sessions = await session_manager.get_user_sessions("test_user")
            assert len(user_sessions) == 3
            
            # Check that the oldest session is closed
            oldest_session = await session_manager.get_session(sessions[0].session_id)
            assert oldest_session is None
        finally:
            await session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_session_expiration(self, session_manager):
        await session_manager.start()
        try:
            # Create a session with short timeout
            session_manager.session_timeout = 1  # 1 second timeout
            session = await session_manager.create_session("test_user")
            
            # Wait for session to expire
            await asyncio.sleep(2)
            
            # Try to get the session
            expired_session = await session_manager.get_session(session.session_id)
            assert expired_session is None
        finally:
            await session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_update_session(self, session_manager):
        await session_manager.start()
        try:
            session = await session_manager.create_session("test_user")
            
            updates = {
                "metadata": {"test_key": "test_value"},
                "llm_provider": "openai"
            }
            
            result = await session_manager.update_session(session.session_id, updates)
            assert result is True
            
            # Verify updates
            updated_session = await session_manager.get_session(session.session_id)
            assert updated_session.metadata["test_key"] == "test_value"
            assert updated_session.llm_provider == "openai"
        finally:
            await session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_add_mcp_server(self, session_manager):
        await session_manager.start()
        try:
            session = await session_manager.create_session("test_user")
            
            result = await session_manager.add_mcp_server_to_session(session.session_id, "file_system")
            assert result is True
            
            updated_session = await session_manager.get_session(session.session_id)
            assert "file_system" in updated_session.mcp_servers
        finally:
            await session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_remove_mcp_server(self, session_manager):
        await session_manager.start()
        try:
            session = await session_manager.create_session("test_user")
            
            # Add server first
            await session_manager.add_mcp_server_to_session(session.session_id, "file_system")
            
            # Remove server
            result = await session_manager.remove_mcp_server_from_session(session.session_id, "file_system")
            assert result is True
            
            updated_session = await session_manager.get_session(session.session_id)
            assert "file_system" not in updated_session.mcp_servers
        finally:
            await session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_session_statistics(self, session_manager):
        await session_manager.start()
        try:
            # Create some sessions
            await session_manager.create_session("user1")
            await session_manager.create_session("user1")
            await session_manager.create_session("user2")
            
            stats = session_manager.get_session_stats()
            
            assert stats["total_sessions"] == 3
            assert stats["active_sessions"] == 3
            assert stats["unique_users"] == 2
            assert stats["user_session_counts"]["user1"] == 2
            assert stats["user_session_counts"]["user2"] == 1
        finally:
            await session_manager.stop()
    
    @pytest.mark.asyncio
    async def test_session_count_methods(self, session_manager):
        await session_manager.start()
        try:
            assert session_manager.get_session_count() == 0
            assert session_manager.get_active_session_count() == 0
            session = await session_manager.create_session("test_user")
            assert session_manager.get_session_count() == 1
            assert session_manager.get_active_session_count() == 1
            # Close session
            session_obj = await session_manager.get_session(session.session_id)
            await session_manager.close_session(session_obj.session_id)
            assert session_manager.get_session_count() == 1
            assert session_manager.get_active_session_count() == 0
        finally:
            await session_manager.stop()


class TestSessionModel:
    """Test cases for Session model."""
    
    def test_session_creation(self):
        """Test creating a Session model."""
        session = Session(user_id="test_user")
        
        assert session.user_id == "test_user"
        assert session.is_active is True
        assert session.session_id is not None
        assert session.created_at is not None
        assert session.last_activity is not None
    
    def test_session_expiration(self):
        """Test session expiration logic."""
        session = Session(user_id="test_user")
        
        # Session should not be expired immediately
        assert session.is_expired(3600) is False
        
        # Create an old session
        old_session = Session(
            user_id="test_user",
            created_at=datetime.utcnow() - timedelta(hours=2),
            last_activity=datetime.utcnow() - timedelta(hours=2)
        )
        
        # Session should be expired
        assert old_session.is_expired(3600) is True
    
    def test_session_activity_update(self):
        """Test updating session activity."""
        session = Session(user_id="test_user")
        old_activity = session.last_activity
        
        # Wait a bit
        import time
        time.sleep(0.1)
        
        session.update_activity()
        
        assert session.last_activity > old_activity
    
    def test_mcp_server_management(self):
        """Test MCP server management in session."""
        session = Session(user_id="test_user")
        
        # Add servers
        session.add_mcp_server("file_system")
        session.add_mcp_server("database")
        
        assert "file_system" in session.mcp_servers
        assert "database" in session.mcp_servers
        assert len(session.mcp_servers) == 2
        
        # Remove server
        session.remove_mcp_server("file_system")
        
        assert "file_system" not in session.mcp_servers
        assert "database" in session.mcp_servers
        assert len(session.mcp_servers) == 1
    
    def test_context_management(self):
        """Test context management in session."""
        session = Session(user_id="test_user")
        
        # Set context
        session.set_context("test_key", "test_value")
        
        assert session.get_context("test_key") == "test_value"
        assert session.get_context("nonexistent", "default") == "default"
    
    def test_metadata_management(self):
        """Test metadata management in session."""
        session = Session(user_id="test_user")
        
        # Set metadata
        session.set_metadata("test_key", "test_value")
        
        assert session.get_metadata("test_key") == "test_value"
        assert session.get_metadata("nonexistent", "default") == "default" 