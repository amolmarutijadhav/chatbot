"""Unit tests for ContextManager."""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.context_manager import ContextManager
from core.models import Session, Context, Message


@pytest.fixture
def mock_session_manager():
    """Create a mock session manager."""
    session_manager = Mock()
    session_manager.get_session = AsyncMock()
    session_manager.update_session = AsyncMock(return_value=True)
    return session_manager


@pytest.fixture
def sample_session():
    """Create a sample session for testing."""
    return Session(
        user_id="test_user",
        session_id="test_session_id",
        context={
            "mcp": {"server1": "active"},
            "llm": {"provider": "openai"},
            "message_history": [
                {"content": "Hello", "role": "user", "timestamp": "2023-01-01T00:00:00Z"}
            ]
        }
    )


class TestContextManager:
    """Test cases for ContextManager."""

    def test_initialization(self, mock_session_manager):
        """Test ContextManager initialization."""
        context_manager = ContextManager(mock_session_manager)
        assert context_manager.session_manager == mock_session_manager

    @pytest.mark.asyncio
    async def test_build_context_success(self, mock_session_manager, sample_session):
        """Test successful context building."""
        mock_session_manager.get_session.return_value = sample_session
        context_manager = ContextManager(mock_session_manager)
        
        context = await context_manager.build_context(
            "test_session_id",
            "Hello, how are you?",
            "chat"
        )
        
        assert context.session_id == "test_session_id"
        assert context.user_id == "test_user"
        assert context.message == "Hello, how are you?"
        assert context.message_type == "chat"
        assert context.correlation_id is not None
        assert len(context.message_history) == 2  # Original + new message

    @pytest.mark.asyncio
    async def test_build_context_session_not_found(self, mock_session_manager):
        """Test context building with non-existent session."""
        mock_session_manager.get_session.return_value = None
        context_manager = ContextManager(mock_session_manager)
        
        with pytest.raises(ValueError, match="Session test_session_id not found"):
            await context_manager.build_context("test_session_id", "Hello", "chat")

    @pytest.mark.asyncio
    async def test_build_context_with_metadata(self, mock_session_manager, sample_session):
        """Test context building with metadata."""
        mock_session_manager.get_session.return_value = sample_session
        context_manager = ContextManager(mock_session_manager)
        
        metadata = {"source": "test", "priority": "high"}
        context = await context_manager.build_context(
            "test_session_id",
            "Hello",
            "chat",
            metadata
        )
        
        assert context.metadata["source"] == "test"
        assert context.metadata["priority"] == "high"

    def test_extract_keywords(self, mock_session_manager):
        """Test keyword extraction."""
        context_manager = ContextManager(mock_session_manager)
        
        # Create a context with some text
        context = Context(
            session_id="test",
            user_id="test_user",
            message="Hello world, this is a test message",
            message_type="chat",
            correlation_id="test-id"
        )
        
        keywords = context_manager.extract_keywords(context)
        
        assert isinstance(keywords, list)
        assert len(keywords) <= 10  # Should return max 10 keywords
        # Should contain meaningful words
        assert any(len(word) > 3 for word in keywords)

    def test_get_context_sentiment_positive(self, mock_session_manager):
        """Test sentiment analysis for positive text."""
        context_manager = ContextManager(mock_session_manager)
        
        context = Context(
            session_id="test",
            user_id="test_user",
            message="This is great and wonderful!",
            message_type="chat",
            correlation_id="test-id"
        )
        
        sentiment = context_manager.get_context_sentiment(context)
        assert sentiment == "positive"

    def test_get_context_sentiment_negative(self, mock_session_manager):
        """Test sentiment analysis for negative text."""
        context_manager = ContextManager(mock_session_manager)
        
        context = Context(
            session_id="test",
            user_id="test_user",
            message="This is terrible and awful!",
            message_type="chat",
            correlation_id="test-id"
        )
        
        sentiment = context_manager.get_context_sentiment(context)
        assert sentiment == "negative"

    def test_get_context_sentiment_neutral(self, mock_session_manager):
        """Test sentiment analysis for neutral text."""
        context_manager = ContextManager(mock_session_manager)
        
        context = Context(
            session_id="test",
            user_id="test_user",
            message="This is a normal message",
            message_type="chat",
            correlation_id="test-id"
        )
        
        sentiment = context_manager.get_context_sentiment(context)
        assert sentiment == "neutral"

    def test_get_context_complexity_high(self, mock_session_manager):
        context_manager = ContextManager(mock_session_manager)
        # Message with 51 words
        message = "word " * 51
        context = Context(
            session_id="test",
            user_id="test_user",
            message=message.strip(),
            message_type="chat",
            correlation_id="test-id"
        )
        complexity = context_manager.get_context_complexity(context)
        assert complexity == "high"

    def test_get_context_complexity_medium(self, mock_session_manager):
        context_manager = ContextManager(mock_session_manager)
        # Message with 21 words
        message = "word " * 21
        context = Context(
            session_id="test",
            user_id="test_user",
            message=message.strip(),
            message_type="chat",
            correlation_id="test-id"
        )
        complexity = context_manager.get_context_complexity(context)
        assert complexity == "medium"

    def test_get_context_complexity_low(self, mock_session_manager):
        """Test complexity analysis for simple text."""
        context_manager = ContextManager(mock_session_manager)
        
        context = Context(
            session_id="test",
            user_id="test_user",
            message="Hello",
            message_type="chat",
            correlation_id="test-id"
        )
        
        complexity = context_manager.get_context_complexity(context)
        assert complexity == "low"

    def test_should_use_mcp_true(self, mock_session_manager):
        """Test MCP usage detection for MCP-related content."""
        context_manager = ContextManager(mock_session_manager)
        
        # Test with MCP request type
        context = Context(
            session_id="test",
            user_id="test_user",
            message="Please read the file config.yaml",
            message_type="mcp_request",
            correlation_id="test-id"
        )
        
        assert context_manager.should_use_mcp(context) is True
        
        # Test with MCP keywords
        context = Context(
            session_id="test",
            user_id="test_user",
            message="Can you list the files in this directory?",
            message_type="chat",
            correlation_id="test-id"
        )
        
        assert context_manager.should_use_mcp(context) is True

    def test_should_use_mcp_false(self, mock_session_manager):
        """Test MCP usage detection for non-MCP content."""
        context_manager = ContextManager(mock_session_manager)
        
        context = Context(
            session_id="test",
            user_id="test_user",
            message="Hello, how are you today?",
            message_type="chat",
            correlation_id="test-id"
        )
        
        assert context_manager.should_use_mcp(context) is False

    def test_get_suggested_mcp_servers_file_system(self, mock_session_manager):
        """Test MCP server suggestions for file system operations."""
        context_manager = ContextManager(mock_session_manager)
        
        context = Context(
            session_id="test",
            user_id="test_user",
            message="Please read the file config.yaml and list the directory contents",
            message_type="chat",
            correlation_id="test-id"
        )
        
        suggestions = context_manager.get_suggested_mcp_servers(context)
        assert "file_system" in suggestions

    def test_get_suggested_mcp_servers_database(self, mock_session_manager):
        """Test MCP server suggestions for database operations."""
        context_manager = ContextManager(mock_session_manager)
        
        context = Context(
            session_id="test",
            user_id="test_user",
            message="Query the database for user data",
            message_type="chat",
            correlation_id="test-id"
        )
        
        suggestions = context_manager.get_suggested_mcp_servers(context)
        assert "database" in suggestions

    def test_get_suggested_mcp_servers_web_search(self, mock_session_manager):
        """Test MCP server suggestions for web search operations."""
        context_manager = ContextManager(mock_session_manager)
        
        context = Context(
            session_id="test",
            user_id="test_user",
            message="Search the web for information about Python",
            message_type="chat",
            correlation_id="test-id"
        )
        
        suggestions = context_manager.get_suggested_mcp_servers(context)
        assert "web_search" in suggestions

    def test_get_suggested_mcp_servers_system(self, mock_session_manager):
        """Test MCP server suggestions for system operations."""
        context_manager = ContextManager(mock_session_manager)
        
        context = Context(
            session_id="test",
            user_id="test_user",
            message="Execute the command ls -la",
            message_type="chat",
            correlation_id="test-id"
        )
        
        suggestions = context_manager.get_suggested_mcp_servers(context)
        assert "system" in suggestions

    def test_get_suggested_mcp_servers_multiple(self, mock_session_manager):
        """Test MCP server suggestions for multiple operation types."""
        context_manager = ContextManager(mock_session_manager)
        
        context = Context(
            session_id="test",
            user_id="test_user",
            message="Read the config file and then search the web for documentation",
            message_type="chat",
            correlation_id="test-id"
        )
        
        suggestions = context_manager.get_suggested_mcp_servers(context)
        assert "file_system" in suggestions
        assert "web_search" in suggestions

    @pytest.mark.asyncio
    async def test_update_context(self, mock_session_manager):
        """Test updating context with new information."""
        context_manager = ContextManager(mock_session_manager)
        
        context = Context(
            session_id="test",
            user_id="test_user",
            message="Hello",
            message_type="chat",
            correlation_id="test-id"
        )
        
        updates = {
            "mcp_context": {"new_server": "active"},
            "llm_context": {"model": "gpt-4"},
            "metadata": {"updated": True}
        }
        
        updated_context = await context_manager.update_context(context, updates)
        
        assert updated_context.mcp_context["new_server"] == "active"
        assert updated_context.llm_context["model"] == "gpt-4"
        assert updated_context.metadata["updated"] is True

    @pytest.mark.asyncio
    async def test_add_message_to_context(self, mock_session_manager):
        context_manager = ContextManager(mock_session_manager)
        context = Context(
            session_id="test",
            user_id="test_user",
            message="Hello",
            message_type="chat",
            correlation_id="test-id"
        )
        new_message = Message(
            content="Response message",
            role="assistant"
        )
        updated_context = await context_manager.add_message_to_context(context, new_message)
        assert len(updated_context.message_history) == 1
        assert updated_context.message_history[0].content == "Response message"
        assert updated_context.message_history[0].role == "assistant"

    @pytest.mark.asyncio
    async def test_get_context_summary(self, mock_session_manager):
        context_manager = ContextManager(mock_session_manager)
        context = Context(
            session_id="test",
            user_id="test_user",
            message="Hello",
            message_type="chat",
            correlation_id="test-id"
        )
        context.mcp_context = {"server1": "active"}
        context.llm_context = {"provider": "openai"}
        context.metadata = {"source": "test"}
        # Add a message to message_history
        context.message_history.append(Message(content="Hello", role="user"))
        summary = await context_manager.get_context_summary(context)
        assert summary["session_id"] == "test"
        assert summary["user_id"] == "test_user"
        assert summary["message_type"] == "chat"
        assert summary["correlation_id"] == "test-id"
        assert summary["message_count"] == 1

    def test_string_representation(self, mock_session_manager):
        """Test string representation of ContextManager."""
        context_manager = ContextManager(mock_session_manager)
        
        str_repr = str(context_manager)
        assert "ContextManager" in str_repr
        assert "session_manager" in str_repr

    def test_repr_representation(self, mock_session_manager):
        """Test repr representation of ContextManager."""
        context_manager = ContextManager(mock_session_manager)
        
        repr_str = repr(context_manager)
        assert "ContextManager" in repr_str
        assert "session_manager" in repr_str 