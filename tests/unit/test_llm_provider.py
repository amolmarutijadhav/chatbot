"""Unit tests for LLM provider classes."""

import pytest
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from llm.llm_provider import LLMProvider
from llm.providers.openai_provider import OpenAIProvider
from core.models import Message, Context


class TestLLMProvider:
    """Test the abstract LLMProvider base class."""

    def test_llm_provider_initialization(self):
        """Test LLMProvider initialization."""
        config = {
            "name": "test_provider",
            "model": "test_model",
            "base_url": "https://test.com",
            "api_key": "test_key",
            "max_tokens": 1000,
            "temperature": 0.7
        }

        # Create a concrete implementation for testing
        class TestProvider(LLMProvider):
            async def connect(self) -> bool:
                return True

            async def disconnect(self) -> bool:
                return True

            async def generate_response(self, messages, context=None, **kwargs) -> str:
                return "Test response"

            async def get_models(self) -> list[str]:
                return ["model1", "model2"]

            async def validate_connection(self) -> bool:
                return True

        provider = TestProvider(config)

        assert provider.name == "test_provider"
        assert provider.model == "test_model"
        assert provider.base_url == "https://test.com"
        assert provider.api_key == "test_key"
        assert provider.max_tokens == 1000
        assert provider.temperature == 0.7
        assert provider.is_connected is False
        assert provider.last_used is None
        assert provider.request_count == 0
        assert provider.error_count == 0

    def test_update_usage_stats(self):
        """Test usage statistics update."""
        config = {"name": "test_provider"}
        
        class TestProvider(LLMProvider):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def generate_response(self, messages, context=None, **kwargs) -> str: return ""
            async def get_models(self) -> list[str]: return []
            async def validate_connection(self) -> bool: return True

        provider = TestProvider(config)
        
        # Test successful request
        provider.update_usage_stats(success=True)
        assert provider.request_count == 1
        assert provider.error_count == 0
        assert provider.last_used is not None

        # Test failed request
        provider.update_usage_stats(success=False)
        assert provider.request_count == 2
        assert provider.error_count == 1

    def test_get_stats(self):
        """Test getting provider statistics."""
        config = {"name": "test_provider", "model": "test_model"}
        
        class TestProvider(LLMProvider):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def generate_response(self, messages, context=None, **kwargs) -> str: return ""
            async def get_models(self) -> list[str]: return []
            async def validate_connection(self) -> bool: return True

        provider = TestProvider(config)
        provider.is_connected = True
        provider.last_used = datetime.utcnow()
        provider.request_count = 5
        provider.error_count = 1

        stats = provider.get_stats()

        assert stats["name"] == "test_provider"
        assert stats["model"] == "test_model"
        assert stats["is_connected"] is True
        assert stats["request_count"] == 5
        assert stats["error_count"] == 1
        assert stats["success_rate"] == 0.8

    def test_format_messages_for_provider(self):
        """Test message formatting for provider."""
        config = {"name": "test_provider"}
        
        class TestProvider(LLMProvider):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def generate_response(self, messages, context=None, **kwargs) -> str: return ""
            async def get_models(self) -> list[str]: return []
            async def validate_connection(self) -> bool: return True

        provider = TestProvider(config)

        messages = [
            Message(content="Hello", role="user"),
            Message(content="Hi there!", role="assistant"),
            Message(content="How can I help?", role="system")
        ]

        formatted = provider.format_messages_for_provider(messages)

        assert len(formatted) == 3
        assert formatted[0]["role"] == "user"
        assert formatted[0]["content"] == "Hello"
        assert formatted[1]["role"] == "assistant"
        assert formatted[1]["content"] == "Hi there!"
        assert formatted[2]["role"] == "system"
        assert formatted[2]["content"] == "How can I help?"

    def test_get_provider_config(self):
        """Test getting provider configuration."""
        config = {
            "name": "test_provider",
            "model": "test_model",
            "base_url": "https://test.com",
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        class TestProvider(LLMProvider):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def generate_response(self, messages, context=None, **kwargs) -> str: return ""
            async def get_models(self) -> list[str]: return []
            async def validate_connection(self) -> bool: return True

        provider = TestProvider(config)

        provider_config = provider.get_provider_config()

        assert provider_config["name"] == "test_provider"
        assert provider_config["model"] == "test_model"
        assert provider_config["base_url"] == "https://test.com"
        assert provider_config["max_tokens"] == 1000
        assert provider_config["temperature"] == 0.7

    def test_string_representation(self):
        """Test string representation."""
        config = {"name": "test_provider", "model": "test_model"}
        
        class TestProvider(LLMProvider):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def generate_response(self, messages, context=None, **kwargs) -> str: return ""
            async def get_models(self) -> list[str]: return []
            async def validate_connection(self) -> bool: return True

        provider = TestProvider(config)
        provider.is_connected = True

        assert str(provider) == "LLMProvider(name=test_provider, model=test_model, connected=True)"
        assert repr(provider) == "LLMProvider(name='test_provider', model='test_model', connected=True)"


class TestOpenAIProvider:
    """Test the OpenAI provider implementation."""

    @pytest.fixture
    def openai_config(self):
        return {
            "name": "openai",
            "model": "gpt-3.5-turbo",
            "base_url": "https://api.openai.com/v1",
            "api_key": "test_key",
            "max_tokens": 1000,
            "temperature": 0.7,
            "api_version": "v1",
            "organization": "test_org"
        }

    @pytest.fixture
    def openai_provider(self, openai_config):
        return OpenAIProvider(openai_config)

    @pytest.mark.asyncio
    async def test_openai_provider_initialization(self, openai_provider, openai_config):
        """Test OpenAI provider initialization."""
        assert openai_provider.name == "openai"
        assert openai_provider.model == "gpt-3.5-turbo"
        assert openai_provider.base_url == "https://api.openai.com/v1"
        assert openai_provider.api_key == "test_key"
        assert openai_provider.api_version == "v1"
        assert openai_provider.organization == "test_org"
        assert openai_provider.session is None
        assert openai_provider.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_success(self, openai_provider):
        """Test successful connection to OpenAI API."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            # Mock successful models response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "data": [
                    {"id": "gpt-3.5-turbo"},
                    {"id": "gpt-4"},
                    {"id": "text-davinci-003"}
                ]
            })
            
            # Setup async context manager for session.get
            mock_session.get.return_value = mock_response
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            result = await openai_provider.connect()

            assert result is True
            assert openai_provider.is_connected is True
            assert openai_provider.session == mock_session

    @pytest.mark.asyncio
    async def test_connect_no_api_key(self, openai_config):
        """Test connection failure when no API key is provided."""
        openai_config["api_key"] = ""
        provider = OpenAIProvider(openai_config)

        result = await provider.connect()

        assert result is False
        assert provider.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_api_error(self, openai_provider):
        """Test connection failure due to API error."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Mock failed models response
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.text = AsyncMock(return_value="Unauthorized")
            mock_session.get.return_value.__aenter__.return_value = mock_response

            result = await openai_provider.connect()

            assert result is False
            assert openai_provider.is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect_success(self, openai_provider):
        """Test successful disconnection."""
        # First connect
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"data": [{"id": "gpt-3.5-turbo"}]})
            mock_session.get.return_value.__aenter__.return_value = mock_response

            await openai_provider.connect()

        # Then disconnect
        result = await openai_provider.disconnect()

        assert result is True
        assert openai_provider.is_connected is False
        assert openai_provider.session is None

    @pytest.mark.asyncio
    async def test_generate_response_success(self, openai_provider):
        """Test successful response generation."""
        # Setup connection
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Mock models response for connection
            mock_models_response = AsyncMock()
            mock_models_response.status = 200
            mock_models_response.json = AsyncMock(return_value={"data": [{"id": "gpt-3.5-turbo"}]})
            mock_session.get.return_value.__aenter__.return_value = mock_models_response

            # Mock chat completion response
            mock_chat_response = AsyncMock()
            mock_chat_response.status = 200
            mock_chat_response.json = AsyncMock(return_value={
                "choices": [{"message": {"content": "Hello! How can I help you?"}}],
                "usage": {"total_tokens": 10}
            })
            mock_session.post.return_value.__aenter__.return_value = mock_chat_response

            await openai_provider.connect()

            # Test response generation
            messages = [Message(content="Hello", role="user")]
            response = await openai_provider.generate_response(messages)

            assert response == "Hello! How can I help you?"
            assert openai_provider.request_count == 1
            assert openai_provider.error_count == 0

    @pytest.mark.asyncio
    async def test_generate_response_not_connected(self, openai_provider):
        """Test response generation when not connected."""
        messages = [Message(content="Hello", role="user")]

        with pytest.raises(ConnectionError, match="OpenAI provider not connected"):
            await openai_provider.generate_response(messages)

    @pytest.mark.asyncio
    async def test_generate_response_api_error(self, openai_provider):
        """Test response generation with API error."""
        # Setup connection
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Mock models response for connection
            mock_models_response = AsyncMock()
            mock_models_response.status = 200
            mock_models_response.json = AsyncMock(return_value={"data": [{"id": "gpt-3.5-turbo"}]})
            mock_session.get.return_value.__aenter__.return_value = mock_models_response

            # Mock failed chat completion response
            mock_chat_response = AsyncMock()
            mock_chat_response.status = 400
            mock_chat_response.text = AsyncMock(return_value="Bad Request")
            mock_session.post.return_value.__aenter__.return_value = mock_chat_response

            await openai_provider.connect()

            # Test response generation
            messages = [Message(content="Hello", role="user")]

            with pytest.raises(Exception, match="OpenAI API error: 400"):
                await openai_provider.generate_response(messages)

            assert openai_provider.request_count == 1
            assert openai_provider.error_count == 1

    @pytest.mark.asyncio
    async def test_get_models_success(self, openai_provider):
        """Test successful model retrieval."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Mock successful models response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "data": [
                    {"id": "gpt-3.5-turbo"},
                    {"id": "gpt-4"},
                    {"id": "text-davinci-003"}
                ]
            })
            mock_session.get.return_value.__aenter__.return_value = mock_response

            models = await openai_provider.get_models()

            assert models == ["gpt-3.5-turbo", "gpt-4", "text-davinci-003"]

    @pytest.mark.asyncio
    async def test_get_models_no_session(self, openai_provider):
        """Test model retrieval when no session exists."""
        models = await openai_provider.get_models()
        assert models == []

    @pytest.mark.asyncio
    async def test_get_models_api_error(self, openai_provider):
        """Test model retrieval with API error."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Mock failed models response
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.text = AsyncMock(return_value="Unauthorized")
            mock_session.get.return_value.__aenter__.return_value = mock_response

            models = await openai_provider.get_models()

            assert models == []

    @pytest.mark.asyncio
    async def test_validate_connection_success(self, openai_provider):
        """Test successful connection validation."""
        with patch.object(openai_provider, 'get_models') as mock_get_models:
            mock_get_models.return_value = ["gpt-3.5-turbo", "gpt-4"]

            result = await openai_provider.validate_connection()

            assert result is True

    @pytest.mark.asyncio
    async def test_validate_connection_failure(self, openai_provider):
        """Test connection validation failure."""
        with patch.object(openai_provider, 'get_models') as mock_get_models:
            mock_get_models.return_value = []

            result = await openai_provider.validate_connection()

            assert result is False

    def test_format_messages_for_provider(self, openai_provider):
        """Test message formatting for OpenAI."""
        messages = [
            Message(content="Hello", role="user"),
            Message(content="Hi there!", role="assistant"),
            Message(content="How can I help?", role="system"),
            Message(content="Unknown role", role="unknown")
        ]

        formatted = openai_provider.format_messages_for_provider(messages)

        assert len(formatted) == 4
        assert formatted[0]["role"] == "user"
        assert formatted[0]["content"] == "Hello"
        assert formatted[1]["role"] == "assistant"
        assert formatted[1]["content"] == "Hi there!"
        assert formatted[2]["role"] == "system"
        assert formatted[2]["content"] == "How can I help?"
        assert formatted[3]["role"] == "user"  # Default for unknown role
        assert formatted[3]["content"] == "Unknown role"

    @pytest.mark.asyncio
    async def test_context_manager(self, openai_provider):
        """Test async context manager."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"data": [{"id": "gpt-3.5-turbo"}]})
            mock_session.get.return_value.__aenter__.return_value = mock_response

            async with openai_provider as provider:
                assert provider.is_connected is True

            assert provider.is_connected is False
            assert provider.session is None 