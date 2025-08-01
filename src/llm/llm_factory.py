"""Factory for creating LLM providers."""

from typing import Dict, Any, Type
from .llm_provider import LLMProvider
from .providers.openai_provider import OpenAIProvider
from utils.logger import get_logger


class LLMFactory:
    """Factory for creating LLM providers."""
    
    # Registry of available providers
    _providers: Dict[str, Type[LLMProvider]] = {
        "openai": OpenAIProvider,
    }
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type[LLMProvider]):
        """Register a new LLM provider."""
        cls._providers[name] = provider_class
        logger = get_logger(__name__)
        logger.info(f"Registered LLM provider: {name}")
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available provider names."""
        return list(cls._providers.keys())
    
    @classmethod
    def create_provider(cls, provider_name: str, config: Dict[str, Any]) -> LLMProvider:
        """Create an LLM provider instance."""
        if provider_name not in cls._providers:
            available = ", ".join(cls.get_available_providers())
            raise ValueError(f"Unknown LLM provider '{provider_name}'. Available: {available}")
        
        provider_class = cls._providers[provider_name]
        
        # Add provider name to config if not present
        if "name" not in config:
            config["name"] = provider_name
        
        try:
            provider = provider_class(config)
            logger = get_logger(__name__)
            logger.info(f"Created LLM provider: {provider_name}")
            return provider
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Failed to create LLM provider '{provider_name}': {e}")
            raise
    
    @classmethod
    def create_provider_from_config(cls, config: Dict[str, Any]) -> LLMProvider:
        """Create an LLM provider from configuration."""
        provider_name = config.get("provider", "openai")
        return cls.create_provider(provider_name, config)
    
    @classmethod
    def validate_provider_config(cls, provider_name: str, config: Dict[str, Any]) -> bool:
        """Validate provider configuration."""
        try:
            provider = cls.create_provider(provider_name, config)
            # Check if required fields are present
            required_fields = ["api_key", "model"]
            for field in required_fields:
                if not config.get(field):
                    logger = get_logger(__name__)
                    logger.error(f"Missing required field '{field}' for provider '{provider_name}'")
                    return False
            return True
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Invalid configuration for provider '{provider_name}': {e}")
            return False 