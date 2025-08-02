"""Unit tests for LLM factory."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from llm.llm_factory import LLMFactory
from llm.llm_provider import LLMProvider
from llm.providers.openai_provider import OpenAIProvider


class TestLLMFactory:
    """Test the LLM factory."""

    def test_get_available_providers(self):
        """Test getting available providers."""
        providers = LLMFactory.get_available_providers()
        
        assert "openai" in providers
        assert isinstance(providers, list)

    def test_register_provider(self):
        """Test registering a new provider."""
        # Create a test provider class
        class TestProvider(LLMProvider):
            async def connect(self) -> bool: return True
            async def disconnect(self) -> bool: return True
            async def generate_response(self, messages, context=None, **kwargs) -> str: return ""
            async def get_models(self) -> list[str]: return []
            async def validate_connection(self) -> bool: return True

        # Register the provider
        LLMFactory.register_provider("test_provider", TestProvider)

        # Check if it's available
        providers = LLMFactory.get_available_providers()
        assert "test_provider" in providers

        # Clean up - remove the test provider
        del LLMFactory._providers["test_provider"]

    def test_create_provider_success(self):
        """Test successful provider creation."""
        config = {
            "name": "openai",
            "model": "gpt-3.5-turbo",
            "api_key": "test_key"
        }

        provider = LLMFactory.create_provider("openai", config)

        assert isinstance(provider, OpenAIProvider)
        assert provider.name == "openai"
        assert provider.model == "gpt-3.5-turbo"
        assert provider.api_key == "test_key"

    def test_create_provider_unknown_provider(self):
        """Test creating provider with unknown name."""
        config = {"name": "unknown"}

        with pytest.raises(ValueError, match="Unknown LLM provider 'unknown'"):
            LLMFactory.create_provider("unknown", config)

    def test_create_provider_from_config(self):
        """Test creating provider from configuration."""
        config = {
            "provider": "openai",
            "name": "openai",
            "model": "gpt-3.5-turbo",
            "api_key": "test_key"
        }

        provider = LLMFactory.create_provider_from_config(config)

        assert isinstance(provider, OpenAIProvider)
        assert provider.name == "openai"

    def test_create_provider_from_config_default(self):
        """Test creating provider from config with default provider."""
        config = {
            "name": "openai",
            "model": "gpt-3.5-turbo",
            "api_key": "test_key"
        }

        provider = LLMFactory.create_provider_from_config(config)

        assert isinstance(provider, OpenAIProvider)
        assert provider.name == "openai"

    def test_create_provider_adds_name_to_config(self):
        """Test that provider name is added to config if not present."""
        config = {
            "model": "gpt-3.5-turbo",
            "api_key": "test_key"
        }

        provider = LLMFactory.create_provider("openai", config)

        assert provider.name == "openai"
        assert config["name"] == "openai"

    def test_create_provider_exception_handling(self):
        """Test exception handling during provider creation."""
        config = {
            "name": "openai",
            "model": "gpt-3.5-turbo",
            "api_key": "test_key"
        }

        # Mock the provider class to raise an exception during instantiation
        original_providers = LLMFactory._providers.copy()
        try:
            LLMFactory._providers["openai"] = Mock(side_effect=Exception("Provider creation failed"))

            with pytest.raises(Exception, match="Provider creation failed"):
                LLMFactory.create_provider("openai", config)
        finally:
            # Restore original providers
            LLMFactory._providers = original_providers

    def test_validate_provider_config_success(self):
        """Test successful provider configuration validation."""
        config = {
            "name": "openai",
            "model": "gpt-3.5-turbo",
            "api_key": "test_key"
        }

        result = LLMFactory.validate_provider_config("openai", config)

        assert result is True

    def test_validate_provider_config_missing_required_fields(self):
        """Test provider configuration validation with missing fields."""
        config = {
            "name": "openai",
            "model": "gpt-3.5-turbo"
            # Missing api_key
        }

        result = LLMFactory.validate_provider_config("openai", config)

        assert result is False

    def test_validate_provider_config_creation_failure(self):
        """Test provider configuration validation with creation failure."""
        config = {
            "name": "openai",
            "model": "gpt-3.5-turbo",
            "api_key": "test_key"
        }

        # Mock the create_provider method to raise an exception
        with patch.object(LLMFactory, 'create_provider') as mock_create:
            mock_create.side_effect = Exception("Creation failed")

            result = LLMFactory.validate_provider_config("openai", config)

            assert result is False

    def test_validate_provider_config_unknown_provider(self):
        """Test provider configuration validation with unknown provider."""
        config = {
            "name": "unknown",
            "model": "test",
            "api_key": "test_key"
        }

        result = LLMFactory.validate_provider_config("unknown", config)

        assert result is False

    def test_factory_singleton_behavior(self):
        """Test that factory maintains singleton-like behavior for providers."""
        config1 = {
            "name": "openai",
            "model": "gpt-3.5-turbo",
            "api_key": "test_key_1"
        }

        config2 = {
            "name": "openai",
            "model": "gpt-4",
            "api_key": "test_key_2"
        }

        provider1 = LLMFactory.create_provider("openai", config1)
        provider2 = LLMFactory.create_provider("openai", config2)

        # Each call should create a new instance
        assert provider1 is not provider2
        assert provider1.api_key == "test_key_1"
        assert provider2.api_key == "test_key_2"

    def test_factory_provider_registry_integrity(self):
        """Test that provider registry maintains integrity."""
        original_providers = LLMFactory._providers.copy()

        # Test that we can't accidentally modify the registry
        try:
            LLMFactory._providers["test"] = None
            assert "test" in LLMFactory._providers
        finally:
            # Clean up
            if "test" in LLMFactory._providers:
                del LLMFactory._providers["test"]

        # Verify original providers are still there
        for provider_name in original_providers:
            assert provider_name in LLMFactory._providers
            assert LLMFactory._providers[provider_name] == original_providers[provider_name]

    def test_factory_error_messages(self):
        """Test that factory provides clear error messages."""
        # Test unknown provider error
        try:
            LLMFactory.create_provider("nonexistent", {})
        except ValueError as e:
            error_msg = str(e)
            assert "Unknown LLM provider 'nonexistent'" in error_msg
            assert "Available:" in error_msg
            assert "openai" in error_msg  # Should list available providers

    def test_factory_config_validation_comprehensive(self):
        """Test comprehensive configuration validation."""
        # Test with all required fields
        valid_config = {
            "name": "openai",
            "model": "gpt-3.5-turbo",
            "api_key": "test_key"
        }
        assert LLMFactory.validate_provider_config("openai", valid_config) is True

        # Test with missing api_key
        invalid_config1 = {
            "name": "openai",
            "model": "gpt-3.5-turbo"
        }
        assert LLMFactory.validate_provider_config("openai", invalid_config1) is False

        # Test with missing model
        invalid_config2 = {
            "name": "openai",
            "api_key": "test_key"
        }
        assert LLMFactory.validate_provider_config("openai", invalid_config2) is False

        # Test with empty config
        assert LLMFactory.validate_provider_config("openai", {}) is False 