"""OpenAI LLM provider implementation."""

import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..llm_provider import LLMProvider
from core.models import Message, Context
from utils.logger import LoggerMixin
from utils.event_bus import publish_event


class OpenAIProvider(LLMProvider, LoggerMixin):
    """OpenAI LLM provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenAI provider."""
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_version = config.get("api_version", "v1")
        self.organization = config.get("organization", "")
        
    async def connect(self) -> bool:
        """Connect to OpenAI API."""
        try:
            if not self.api_key:
                self.logger.error("OpenAI API key not provided")
                return False
            
            # Create aiohttp session
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            # Test connection by getting models
            models = await self.get_models()
            if models:
                self.is_connected = True
                self.logger.info(f"Connected to OpenAI API. Available models: {len(models)}")
                
                # Publish event
                publish_event("llm_provider_connected", {
                    "provider": "openai",
                    "models_count": len(models),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return True
            else:
                self.logger.error("Failed to connect to OpenAI API - no models available")
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to OpenAI API: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from OpenAI API."""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            self.is_connected = False
            self.logger.info("Disconnected from OpenAI API")
            
            # Publish event
            publish_event("llm_provider_disconnected", {
                "provider": "openai",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from OpenAI API: {e}")
            return False
    
    async def generate_response(
        self, 
        messages: List[Message], 
        context: Optional[Context] = None,
        **kwargs
    ) -> str:
        """Generate response using OpenAI API."""
        if not self.is_connected or not self.session:
            raise ConnectionError("OpenAI provider not connected")
        
        try:
            # Format messages for OpenAI API
            formatted_messages = self.format_messages_for_provider(messages)
            
            # Prepare request payload
            payload = {
                "model": self.model,
                "messages": formatted_messages,
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
                "stream": False
            }
            
            # Add optional parameters
            if "top_p" in kwargs:
                payload["top_p"] = kwargs["top_p"]
            if "frequency_penalty" in kwargs:
                payload["frequency_penalty"] = kwargs["frequency_penalty"]
            if "presence_penalty" in kwargs:
                payload["presence_penalty"] = kwargs["presence_penalty"]
            
            # Make API request
            url = f"{self.base_url}/chat/completions"
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]
                    
                    # Update stats
                    self.update_usage_stats(success=True)
                    
                    # Publish event
                    publish_event("llm_response_generated", {
                        "provider": "openai",
                        "model": self.model,
                        "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    return content
                else:
                    error_text = await response.text()
                    self.logger.error(f"OpenAI API error: {response.status} - {error_text}")
                    self.update_usage_stats(success=False)
                    raise Exception(f"OpenAI API error: {response.status} - {error_text}")
                    
        except Exception as e:
            self.logger.error(f"Error generating response from OpenAI: {e}")
            self.update_usage_stats(success=False)
            raise
    
    async def get_models(self) -> List[str]:
        """Get available OpenAI models."""
        if not self.session:
            return []
        
        try:
            url = f"{self.base_url}/models"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model["id"] for model in data["data"]]
                    return models
                else:
                    self.logger.error(f"Failed to get OpenAI models: {response.status}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Error getting OpenAI models: {e}")
            return []
    
    async def validate_connection(self) -> bool:
        """Validate connection to OpenAI API."""
        try:
            models = await self.get_models()
            return len(models) > 0
        except Exception:
            return False
    
    def format_messages_for_provider(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Format messages specifically for OpenAI API."""
        formatted_messages = []
        
        for message in messages:
            # OpenAI supports: system, user, assistant
            role = message.role
            if role not in ["system", "user", "assistant"]:
                role = "user"  # Default to user if role not recognized
            
            formatted_messages.append({
                "role": role,
                "content": message.content
            })
        
        return formatted_messages
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect() 