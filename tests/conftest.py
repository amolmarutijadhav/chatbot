"""Shared pytest configuration and fixtures for all test types."""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Add src to Python path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.config_manager import ConfigurationManager
from utils.event_bus import EventBus, get_event_bus
from utils.logger import setup_logging, get_logger
from core.session_manager import SessionManager
from core.context_manager import ContextManager


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def clear_event_bus():
    """Clear event bus history and subscribers before each test."""
    bus = get_event_bus()
    bus.clear_event_history()
    bus._subscribers.clear()
    bus._async_subscribers.clear()
    yield
    bus.clear_event_history()
    bus._subscribers.clear()
    bus._async_subscribers.clear()


@pytest.fixture
def base_config():
    """Base configuration for testing."""
    return {
        "chatbot": {
            "name": "Test Chatbot",
            "version": "1.0.0"
        },
        "session": {
            "max_sessions_per_user": 5,
            "timeout": 3600,
            "cleanup_interval": 300
        },
        "logging": {
            "level": "INFO",
            "structured": True,
            "console_output": False  # Disable console output during tests
        },
        "api": {
            "host": "localhost",
            "port": 8000
        },
        "llm": {
            "default_provider": "openai",
            "providers": {
                "openai": {
                    "api_key": "test-key",
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-4"
                }
            }
        },
        "mcp": {
            "servers": {
                "file_system": {
                    "type": "stdio",
                    "command": "echo 'test'"
                }
            }
        }
    }


@pytest.fixture
def config_manager(base_config):
    """Create a configuration manager with test configuration."""
    config = ConfigurationManager()
    config.config = base_config.copy()
    return config


@pytest.fixture
def session_manager(base_config):
    """Create a session manager for testing."""
    return SessionManager(base_config["session"])


@pytest.fixture
def context_manager(session_manager):
    """Create a context manager for testing."""
    return ContextManager(session_manager)


@pytest.fixture
def event_bus():
    """Get the event bus instance."""
    return get_event_bus()


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider for testing."""
    mock_provider = Mock()
    mock_provider.generate_response = AsyncMock(return_value="Mock response")
    mock_provider.get_models = AsyncMock(return_value=["gpt-4", "gpt-3.5-turbo"])
    return mock_provider


@pytest.fixture
def mock_mcp_server():
    """Create a mock MCP server for testing."""
    mock_server = Mock()
    mock_server.name = "test_server"
    mock_server.is_connected = True
    mock_server.send_request = AsyncMock(return_value={"result": "test_result"})
    mock_server.connect = AsyncMock(return_value=True)
    mock_server.disconnect = AsyncMock(return_value=True)
    return mock_server


@pytest.fixture
def sample_session_data():
    """Sample session data for testing."""
    return {
        "user_id": "test_user",
        "session_id": "test-session-123",
        "created_at": "2024-01-01T00:00:00",
        "last_activity": "2024-01-01T00:00:00",
        "is_active": True,
        "mcp_servers": ["file_system"],
        "llm_provider": "openai",
        "metadata": {"source": "test"}
    }


@pytest.fixture
def sample_context_data():
    """Sample context data for testing."""
    return {
        "session_id": "test-session-123",
        "user_id": "test_user",
        "message": "Hello, this is a test message",
        "message_type": "chat",
        "correlation_id": "test-correlation-123",
        "mcp_context": {"server1": "active"},
        "llm_context": {"provider": "openai"},
        "metadata": {"source": "test"}
    }


@pytest.fixture
def sample_message_data():
    """Sample message data for testing."""
    return {
        "content": "This is a test message",
        "role": "user",
        "metadata": {"source": "test"}
    }


# Integration test specific fixtures
@pytest.fixture
def integration_config(base_config):
    """Configuration specifically for integration tests."""
    config = base_config.copy()
    config["session"]["max_sessions_per_user"] = 10  # Higher limit for integration tests
    config["session"]["timeout"] = 7200  # Longer timeout
    return config


@pytest.fixture
def integration_session_manager(integration_config):
    """Session manager for integration tests."""
    return SessionManager(integration_config["session"])


@pytest.fixture
def integration_context_manager(integration_session_manager):
    """Context manager for integration tests."""
    return ContextManager(integration_session_manager)


# E2E test specific fixtures
@pytest.fixture
def e2e_config(base_config):
    """Configuration specifically for E2E tests."""
    config = base_config.copy()
    config["session"]["max_sessions_per_user"] = 3  # Lower limit to test cleanup
    config["session"]["timeout"] = 1800  # Shorter timeout to test expiration
    config["logging"]["console_output"] = True  # Enable console output for E2E
    return config


@pytest.fixture
def e2e_session_manager(e2e_config):
    """Session manager for E2E tests."""
    return SessionManager(e2e_config["session"])


@pytest.fixture
def e2e_context_manager(e2e_session_manager):
    """Context manager for E2E tests."""
    return ContextManager(e2e_session_manager)


# Performance test fixtures
@pytest.fixture
def performance_config(base_config):
    """Configuration for performance tests."""
    config = base_config.copy()
    config["session"]["max_sessions_per_user"] = 100  # High limit for performance tests
    config["session"]["timeout"] = 3600
    return config


@pytest.fixture
def performance_session_manager(performance_config):
    """Session manager for performance tests."""
    return SessionManager(performance_config["session"])


@pytest.fixture
def performance_context_manager(performance_session_manager):
    """Context manager for performance tests."""
    return ContextManager(performance_session_manager)


# Utility fixtures
@pytest.fixture
def setup_logging_for_tests():
    """Setup logging for tests."""
    setup_logging(
        level="INFO",
        structured=True,
        console_output=False
    )
    yield
    # Cleanup if needed


@pytest.fixture
def correlation_id():
    """Generate a correlation ID for testing."""
    import uuid
    return str(uuid.uuid4())


# Test data generators
@pytest.fixture
def generate_test_users():
    """Generate test user IDs."""
    def _generate_users(count=5):
        return [f"test_user_{i}" for i in range(count)]
    return _generate_users


@pytest.fixture
def generate_test_messages():
    """Generate test messages."""
    def _generate_messages(count=5):
        return [
            f"This is test message number {i} for testing purposes."
            for i in range(count)
        ]
    return _generate_messages


@pytest.fixture
def generate_test_sessions():
    """Generate test session data."""
    def _generate_sessions(user_count=3, sessions_per_user=2):
        sessions = []
        for user_id in range(user_count):
            for session_id in range(sessions_per_user):
                sessions.append({
                    "user_id": f"user_{user_id}",
                    "session_id": f"session_{user_id}_{session_id}",
                    "metadata": {"test": True}
                })
        return sessions
    return _generate_sessions 