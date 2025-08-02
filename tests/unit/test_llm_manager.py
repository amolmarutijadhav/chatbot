"""Unit tests for LLM manager."""

import pytest
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from llm.llm_manager import LLMManager
from llm.providers.openai_provider import OpenAIProvider
from core.models import Message, Context


class TestLLMManager:
    """Test the LLM manager."""

    @pytest.fixture
    def llm_config(self):
        return {
            "default_provider": "openai",
            "fallback_providers": ["anthropic"],
            "load_balancing": "round_robin",
            "health_check_interval": 300,
            "providers": {
                "openai": {
                    "name": "openai",
                    "model": "gpt-3.5-turbo",
                    "base_url": "https://api.openai.com/v1",
                    "api_key": "test_key",
                    "max_tokens": 1000,
                    "temperature": 0.7
                },
                "anthropic": {
                    "name": "anthropic",
                    "model": "claude-3-sonnet",
                    "base_url": "https://api.anthropic.com",
                    "api_key": "test_key_2",
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            }
        }

    @pytest.fixture
    def llm_manager(self, llm_config):
        return LLMManager(llm_config)

    @pytest.mark.asyncio
    async def test_llm_manager_initialization(self, llm_manager, llm_config):
        """Test LLM manager initialization."""
        assert llm_manager.config == llm_config
        assert llm_manager.default_provider == "openai"
        assert llm_manager.fallback_providers == ["anthropic"]
        assert llm_manager.load_balancing == "round_robin"
        assert llm_manager.health_check_interval == 300
        assert llm_manager.providers == {}
        assert llm_manager.health_check_task is None

    @pytest.mark.asyncio
    async def test_start_success(self, llm_manager):
        """Test successful start of LLM manager."""
        with patch.object(llm_manager, 'add_provider') as mock_add_provider:
            mock_add_provider.return_value = True

            await llm_manager.start()

            assert mock_add_provider.call_count == 2
            assert llm_manager.health_check_task is not None

            # Cleanup
            if llm_manager.health_check_task:
                llm_manager.health_check_task.cancel()
                try:
                    await llm_manager.health_check_task
                except asyncio.CancelledError:
                    pass

    @pytest.mark.asyncio
    async def test_start_with_provider_failure(self, llm_manager):
        """Test start with provider connection failure."""
        with patch.object(llm_manager, 'add_provider') as mock_add_provider:
            mock_add_provider.return_value = False

            await llm_manager.start()

            assert mock_add_provider.call_count == 2
            assert len(llm_manager.providers) == 0

    @pytest.mark.asyncio
    async def test_stop_success(self, llm_manager):
        """Test successful stop of LLM manager."""
        # First start
        with patch.object(llm_manager, 'add_provider') as mock_add_provider:
            mock_add_provider.return_value = True
            await llm_manager.start()

        # Add some mock providers
        mock_provider1 = AsyncMock()
        mock_provider2 = AsyncMock()
        llm_manager.providers["provider1"] = mock_provider1
        llm_manager.providers["provider2"] = mock_provider2

        # Then stop
        await llm_manager.stop()

        # Verify providers were disconnected and cleared
        mock_provider1.disconnect.assert_called_once()
        mock_provider2.disconnect.assert_called_once()
        assert len(llm_manager.providers) == 0
        # Check that health check task is cancelled (not None)
        assert llm_manager.health_check_task is None or llm_manager.health_check_task.cancelled()

    @pytest.mark.asyncio
    async def test_add_provider_success(self, llm_manager):
        """Test successful provider addition."""
        with patch('llm.llm_factory.LLMFactory.validate_provider_config') as mock_validate:
            with patch('llm.llm_factory.LLMFactory.create_provider') as mock_create:
                mock_validate.return_value = True
                mock_provider = AsyncMock()
                mock_provider.connect.return_value = True
                mock_create.return_value = mock_provider

                result = await llm_manager.add_provider("test_provider", {"name": "test"})

                assert result is True
                assert "test_provider" in llm_manager.providers
                assert llm_manager.providers["test_provider"] == mock_provider

    @pytest.mark.asyncio
    async def test_add_provider_validation_failure(self, llm_manager):
        """Test provider addition with validation failure."""
        with patch('llm.llm_factory.LLMFactory.validate_provider_config') as mock_validate:
            mock_validate.return_value = False

            result = await llm_manager.add_provider("test_provider", {"name": "test"})

            assert result is False
            assert "test_provider" not in llm_manager.providers

    @pytest.mark.asyncio
    async def test_add_provider_connection_failure(self, llm_manager):
        """Test provider addition with connection failure."""
        with patch('llm.llm_factory.LLMFactory.validate_provider_config') as mock_validate:
            with patch('llm.llm_factory.LLMFactory.create_provider') as mock_create:
                mock_validate.return_value = True
                mock_provider = AsyncMock()
                mock_provider.connect.return_value = False
                mock_create.return_value = mock_provider

                result = await llm_manager.add_provider("test_provider", {"name": "test"})

                assert result is False
                assert "test_provider" not in llm_manager.providers

    @pytest.mark.asyncio
    async def test_remove_provider_success(self, llm_manager):
        """Test successful provider removal."""
        # First add a provider
        mock_provider = AsyncMock()
        llm_manager.providers["test_provider"] = mock_provider

        result = await llm_manager.remove_provider("test_provider")

        assert result is True
        assert "test_provider" not in llm_manager.providers
        mock_provider.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_nonexistent_provider(self, llm_manager):
        """Test removal of nonexistent provider."""
        result = await llm_manager.remove_provider("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_generate_response_success(self, llm_manager):
        """Test successful response generation."""
        # Setup providers
        mock_provider1 = AsyncMock()
        mock_provider1.is_connected = True
        mock_provider1.generate_response.return_value = "Response from provider 1"

        mock_provider2 = AsyncMock()
        mock_provider2.is_connected = True
        mock_provider2.generate_response.return_value = "Response from provider 2"

        llm_manager.providers["openai"] = mock_provider1
        llm_manager.providers["anthropic"] = mock_provider2

        messages = [Message(content="Hello", role="user")]

        response = await llm_manager.generate_response(messages)

        assert response == "Response from provider 1"
        mock_provider1.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_response_with_specific_provider(self, llm_manager):
        """Test response generation with specific provider."""
        mock_provider = AsyncMock()
        mock_provider.is_connected = True
        mock_provider.generate_response.return_value = "Specific response"

        llm_manager.providers["anthropic"] = mock_provider

        messages = [Message(content="Hello", role="user")]

        response = await llm_manager.generate_response(messages, provider_name="anthropic")

        assert response == "Specific response"
        mock_provider.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_response_provider_not_found(self, llm_manager):
        """Test response generation with provider not found."""
        # Add a provider so the "no providers available" check passes
        mock_provider = AsyncMock()
        mock_provider.is_connected = True
        llm_manager.providers["existing_provider"] = mock_provider
        
        messages = [Message(content="Hello", role="user")]

        with pytest.raises(ValueError, match="Provider 'nonexistent' not found"):
            await llm_manager.generate_response(messages, provider_name="nonexistent")

    @pytest.mark.asyncio
    async def test_generate_response_no_providers(self, llm_manager):
        """Test response generation with no providers available."""
        messages = [Message(content="Hello", role="user")]

        with pytest.raises(RuntimeError, match="No LLM providers available"):
            await llm_manager.generate_response(messages)

    @pytest.mark.asyncio
    async def test_generate_response_with_fallback(self, llm_manager):
        """Test response generation with fallback to second provider."""
        # Setup providers
        mock_provider1 = AsyncMock()
        mock_provider1.is_connected = True
        mock_provider1.generate_response.side_effect = Exception("Provider 1 failed")

        mock_provider2 = AsyncMock()
        mock_provider2.is_connected = True
        mock_provider2.generate_response.return_value = "Response from provider 2"

        llm_manager.providers["openai"] = mock_provider1
        llm_manager.providers["anthropic"] = mock_provider2

        messages = [Message(content="Hello", role="user")]

        response = await llm_manager.generate_response(messages)

        assert response == "Response from provider 2"
        mock_provider1.generate_response.assert_called_once()
        mock_provider2.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_response_all_providers_fail(self, llm_manager):
        """Test response generation when all providers fail."""
        # Setup providers
        mock_provider1 = AsyncMock()
        mock_provider1.is_connected = True
        mock_provider1.generate_response.side_effect = Exception("Provider 1 failed")

        mock_provider2 = AsyncMock()
        mock_provider2.is_connected = True
        mock_provider2.generate_response.side_effect = Exception("Provider 2 failed")

        llm_manager.providers["openai"] = mock_provider1
        llm_manager.providers["anthropic"] = mock_provider2

        messages = [Message(content="Hello", role="user")]

        with pytest.raises(RuntimeError, match="All LLM providers failed"):
            await llm_manager.generate_response(messages)

    def test_get_provider_priority_list(self, llm_manager):
        """Test getting provider priority list."""
        # Setup providers
        mock_provider1 = AsyncMock()
        mock_provider2 = AsyncMock()
        mock_provider3 = AsyncMock()

        llm_manager.providers["openai"] = mock_provider1
        llm_manager.providers["anthropic"] = mock_provider2
        llm_manager.providers["other"] = mock_provider3

        priority_list = llm_manager._get_provider_priority_list()

        # Should have default provider first, then fallback, then others
        expected_order = ["openai", "anthropic", "other"]
        assert priority_list == expected_order

    @pytest.mark.asyncio
    async def test_get_provider_stats(self, llm_manager):
        """Test getting provider statistics."""
        # Setup providers
        mock_provider1 = AsyncMock()
        mock_provider1.is_connected = True
        mock_provider1.get_stats.return_value = {
            "name": "openai",
            "request_count": 10,
            "error_count": 1
        }

        mock_provider2 = AsyncMock()
        mock_provider2.is_connected = False
        mock_provider2.get_stats.return_value = {
            "name": "anthropic",
            "request_count": 5,
            "error_count": 0
        }

        llm_manager.providers["openai"] = mock_provider1
        llm_manager.providers["anthropic"] = mock_provider2

        stats = await llm_manager.get_provider_stats()

        assert stats["total_providers"] == 2
        assert stats["connected_providers"] == 1
        assert "openai" in stats["providers"]
        assert "anthropic" in stats["providers"]

    @pytest.mark.asyncio
    async def test_health_check_success(self, llm_manager):
        """Test successful health check."""
        # Setup providers
        mock_provider1 = AsyncMock()
        mock_provider1.is_connected = True
        mock_provider1.validate_connection.return_value = True

        mock_provider2 = AsyncMock()
        mock_provider2.is_connected = True
        mock_provider2.validate_connection.return_value = False

        llm_manager.providers["openai"] = mock_provider1
        llm_manager.providers["anthropic"] = mock_provider2

        health_status = await llm_manager.health_check()

        assert health_status["openai"] is True
        assert health_status["anthropic"] is False

    @pytest.mark.asyncio
    async def test_health_check_with_reconnection(self, llm_manager):
        """Test health check with provider reconnection."""
        # Setup provider
        mock_provider = AsyncMock()
        mock_provider.is_connected = True
        mock_provider.validate_connection.return_value = False

        llm_manager.providers["openai"] = mock_provider

        await llm_manager.health_check()

        # Should attempt to disconnect and reconnect
        mock_provider.disconnect.assert_called_once()
        mock_provider.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_loop(self, llm_manager):
        """Test health check loop."""
        with patch.object(llm_manager, 'health_check') as mock_health_check:
            mock_health_check.return_value = {}

            # Start health check task
            llm_manager.health_check_interval = 0.1
            task = asyncio.create_task(llm_manager._health_check_loop())

            # Wait a bit for the loop to run
            await asyncio.sleep(0.2)

            # Cancel the task
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

            # Should have called health_check at least once
            assert mock_health_check.call_count >= 1

    def test_get_provider(self, llm_manager):
        """Test getting a specific provider."""
        mock_provider = AsyncMock()
        llm_manager.providers["test_provider"] = mock_provider

        provider = llm_manager.get_provider("test_provider")
        assert provider == mock_provider

        # Test nonexistent provider
        provider = llm_manager.get_provider("nonexistent")
        assert provider is None

    def test_list_providers(self, llm_manager):
        """Test listing all providers."""
        llm_manager.providers["provider1"] = AsyncMock()
        llm_manager.providers["provider2"] = AsyncMock()

        providers = llm_manager.list_providers()
        assert set(providers) == {"provider1", "provider2"}

    def test_is_provider_available(self, llm_manager):
        """Test checking if provider is available."""
        mock_provider = AsyncMock()
        mock_provider.is_connected = True
        llm_manager.providers["test_provider"] = mock_provider

        assert llm_manager.is_provider_available("test_provider") is True

        # Test disconnected provider
        mock_provider.is_connected = False
        assert llm_manager.is_provider_available("test_provider") is False

        # Test nonexistent provider
        assert llm_manager.is_provider_available("nonexistent") is False

    @pytest.mark.asyncio
    async def test_context_manager(self, llm_manager):
        """Test async context manager."""
        with patch.object(llm_manager, 'start') as mock_start:
            with patch.object(llm_manager, 'stop') as mock_stop:
                async with llm_manager as manager:
                    assert manager == llm_manager

                mock_start.assert_called_once()
                mock_stop.assert_called_once() 