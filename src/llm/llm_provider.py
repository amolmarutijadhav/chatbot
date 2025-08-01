"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.models import Message, Context


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the LLM provider with configuration."""
        self.config = config
        self.name = config.get("name", "unknown")
        self.model = config.get("model", "default")
        self.base_url = config.get("base_url", "")
        self.api_key = config.get("api_key", "")
        self.max_tokens = config.get("max_tokens", 1000)
        self.temperature = config.get("temperature", 0.7)
        self.is_connected = False
        self.last_used = None
        self.request_count = 0
        self.error_count = 0
        
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the LLM service."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the LLM service."""
        pass
    
    @abstractmethod
    async def generate_response(
        self, 
        messages: List[Message], 
        context: Optional[Context] = None,
        **kwargs
    ) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def get_models(self) -> List[str]:
        """Get available models for this provider."""
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate the connection to the LLM service."""
        pass
    
    def update_usage_stats(self, success: bool = True):
        """Update usage statistics."""
        self.last_used = datetime.utcnow()
        self.request_count += 1
        if not success:
            self.error_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics."""
        return {
            "name": self.name,
            "model": self.model,
            "is_connected": self.is_connected,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "success_rate": (self.request_count - self.error_count) / max(self.request_count, 1)
        }
    
    def format_messages_for_provider(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Format messages for the specific provider's API."""
        formatted_messages = []
        for message in messages:
            formatted_messages.append({
                "role": message.role,
                "content": message.content
            })
        return formatted_messages
    
    def get_provider_config(self) -> Dict[str, Any]:
        """Get provider-specific configuration."""
        return {
            "name": self.name,
            "model": self.model,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
    
    def __str__(self) -> str:
        return f"LLMProvider(name={self.name}, model={self.model}, connected={self.is_connected})"
    
    def __repr__(self) -> str:
        return f"LLMProvider(name='{self.name}', model='{self.model}', connected={self.is_connected})" 